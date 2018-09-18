from math import degrees, radians
import socket
import time
import logging
import threading
import atexit

import bpy
from enum import Enum

from . import handheld_panel

log = logging.getLogger(__name__)
# set verbosity level
log.setLevel(level=logging.DEBUG)


# running script multiple times adds new handler every time
# if len(log.handlers) == 0:
#     console_handler = logging.StreamHandler()
#     # console_handler.setLevel(logging.DEBUG)  # set verbosity level for handler
#     formatter = logging.Formatter('%(levelname)s:%(threadName)s:%(message)s')
#     console_handler.setFormatter(formatter)
#     log.addHandler(console_handler)


class HandheldClient(threading.Thread):

    def __init__(self, context, acc_transform=None, rot_transform=None, time_transform=None):
        threading.Thread.__init__(self, daemon=True)
        self.handheld_data = context.scene.handheld_data
        # for stopping receiving loop
        self._receiving = False
        # for syncing access to deltas
        self.lock_loc_rot = threading.Lock()
        self._speed_loc = [0., 0., 0.]
        self._delta_loc = [0., 0., 0.]
        self._speed_rot = [0., 0., 0.]
        self._delta_rot = [0., 0., 0.]
        self._last_delta_update_time = None
        self._last_parsed_packet_time = None  # used for calculating location from acceleration
        # income data may need some user defined processing 
        self.acc_transform = acc_transform
        self.rot_transform = rot_transform
        self.time_transform = time_transform
        self.partial_datagram = None
        self.connection_state = ConnectionState.INIT
        self.gravity_compensation = None
        self.packet_counter = 0
        self.mean = [0, 0, 0]
        atexit.register(self.stop)

    @property
    def delta_loc(self):
        """Getter: reset delta location to [0, 0, 0] and return original"""
        self.update_loc_rot_delta()
        tmp = self._delta_loc
        with self.lock_loc_rot:
            self._delta_loc = [0, 0, 0]
        return [0,0,0]

    @delta_loc.setter
    def delta_loc(self, value):
        """Setter: 3 element iterable required """
        for i in range(len(self._delta_loc)):
            self._delta_loc[i] = float(value[i])

    @property
    def delta_rot(self):
        """Getter: reset delta rotation to [0, 0, 0] and return original"""
        self.update_loc_rot_delta()
        tmp = self._delta_rot
        with self.lock_loc_rot:
            self._delta_rot = [0, 0, 0]
        return tmp

    @delta_rot.setter
    def delta_rot(self, value):
        """Setter: 3 element iterable required (degrees)"""
        for i in range(len(self._delta_rot)):
            self._delta_rot[i] = float(value[i])

    def start(self):
        self._receiving = True
        threading.Thread.start(self)

    def stop(self):
        self._receiving = False

    def run(self):
        """Establishes connection, receives and parses data until self.stop() is called.
           Updates delta_loc and delta_rot based on received data
        """
        client = socket.socket()
        self.connection_state = ConnectionState.INIT
        try:
            client.connect((self.handheld_data.host, self.handheld_data.port))
            self.connection_state = ConnectionState.CONNECTING
        except (socket.error, OSError, ConnectionError):
            log.exception("Unable to open connection")
            self.connection_state = ConnectionState.FAILED
        else:
            log.info("Connection established with: " + self.handheld_data.host)
            self.connection_state = ConnectionState.SUCCESS
            handheld_panel.is_connected = True

            first_run = True
            while self._receiving:
                data = client.recv(1024).decode()
                if data is '':
                    self._receiving = False

                # formated_data = ''
                # for char in data.split('\r\n'):
                #     if char != '':
                #         formated_data += chr(int(char))

                # log.debug("formatted data:\n" + data)
                self.parse_data(data, first_run)
                first_run = False

            client.close()
            self.connection_state = ConnectionState.CLOSED
            log.info("Connection closed({})".format(self.handheld_data.host))

    def parse_data(self, data, first_run):
        """Split income data into single datagrams, calculate and apply deltas to delta_loc, delta_rot"""
        # data ends with ';' what leaves empty string at the end 
        data = data.split(';')
        for i, single_datagram in enumerate(data):
            # dummy datagram caused if message end with ';'
            if single_datagram == '' or single_datagram == '\r\n':
                continue

            # TODO: handle partial datagrams
            if len(single_datagram.split()) != 7:
                log.debug("invalid packet length:: {}".format(single_datagram))
                continue
                # if i == 0:
                #     if first_run:
                #         continue
                #     if self.partial_datagram is not None:
                #         single_datagram = self.partial_datagram + '' + single_datagram
                #     else:
                #         continue
                #
                # if i == (len(data) - 1):
                #     self.partial_datagram = single_datagram
                #     continue

            try:
                loc_acc, rot_speed, current_time = self.parse_single_datagram(single_datagram)
            except ValueError as e:
                log.exception("Parse error: {}".format(single_datagram))
            else:
                if self.packet_counter > 10:
                    self.update_loc_rot_speed(loc_acc, rot_speed, current_time)

            log.debug(
                "current loc speed: {:.2f}, {:.2f}, {:.2f}, rot speed: {:.2f}, {:.2f}, {:.2f}, \n"
                "data: {} ::\n"
                " {}, {}, {}\n".format(
                    self._speed_loc[0],
                    self._speed_loc[1],
                    self._speed_loc[2],
                    self._speed_rot[0],
                    self._speed_rot[1],
                    self._speed_rot[2],
                    single_datagram,
                    list(loc_acc), list(rot_speed), current_time))

    def parse_single_datagram(self, single_datagram):
        data = single_datagram.split()
        loc_acc = [float(i) for i in data[0:3]]
        rot_speed = [float(i) for i in data[3:6]]
        current_time = float(data[6])
        self.packet_counter += 1

        # apply user defined functions if exist
        if self.acc_transform is not None:
            loc_acc = self.acc_transform(loc_acc)

        if self.rot_transform is not None:
            rot_speed = self.rot_transform(rot_speed)

        if self.time_transform is not None:
            current_time = self.time_transform(current_time)

        # first 10 incoming datagrams is used for gravity compensation
        if self.gravity_compensation is None:
            if self.packet_counter >= 10:
                self.gravity_compensation = [-i / (self.packet_counter-1) for i in self.mean]  # [-i for i in loc_acc]
            else:
                self.mean = [i + j for i, j in zip(self.mean, loc_acc)]
        else:
            loc_acc = [a + g for a, g in zip(loc_acc, self.gravity_compensation)]

        return loc_acc, rot_speed, current_time

    def update_loc_rot_speed(self, loc_acc, rot_speed, current_time):
        """Changes loc, rot acceleration to current speed: v = a*t, - constant interpolation"""
        if self._last_parsed_packet_time is None:
            self._last_parsed_packet_time = current_time
            return [0, 0, 0]
        time_delta = current_time - self._last_parsed_packet_time
        self._last_parsed_packet_time = current_time

        if time_delta > 1 or time_delta < 0:
            return

        with self.lock_loc_rot:
            for i, a in enumerate(loc_acc):
                self._speed_loc[i] += a * time_delta

            for i, a in enumerate(rot_speed):
                self._speed_rot[i] = a

    def update_loc_rot_delta(self):
        current_time = time.time()
        if self._last_delta_update_time is None:
            self._last_delta_update_time = current_time
            return
        time_delta = current_time - self._last_delta_update_time
        self._last_delta_update_time = current_time

        with self.lock_loc_rot:
            for i, xyz in enumerate(self._speed_loc):
                self._delta_loc[i] += xyz * time_delta * self.handheld_data.scale

            for i, xyz in enumerate(self._speed_rot):
                self._delta_rot[i] += xyz * time_delta


class HandheldAnimate(bpy.types.Operator):
    """Main operator responsible for starting client thread, shortcuts, handling teardown """
    bl_idname = "handheld.animate"
    bl_label = "Modal Timer Operator"

    status = "Connect"  # used for button in panel
    running = False  # used for poll func only
    connection_thread = None
    timer = None
    handler_exists = False

    @classmethod
    def poll(cls, context):
        """ Disable creating new instances of operator if operator is running """
        return not HandheldAnimate.running and context.area.type == 'VIEW_3D'

    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if self.connection_thread.connection_state == ConnectionState.FAILED:
            # detect error in socket. Not ideal though...
            self.report({'ERROR'}, "Connection dead, look at the console")
            self.cancel(context)
            return {'CANCELLED'}

        status_text = '(ESC) to exit, '
        if self.handler_exists:
            status_text += "(Y) to stop playback, "
        else:
            status_text += "(Y) to start animation, "

        if event.type == 'Y' and event.value == 'PRESS':
            log.info(
                "timer: {}, handler: {}, event: {}-{}".format(self.timer, self.handler_exists, event.type,
                                                              event.value))
            if not self.handler_exists:
                log.debug("Switching to per frame update")
                HandheldAnimate.status = "Running on frame changed"
                bpy.app.handlers.frame_change_pre.append(self.update_object_on_frame_changed)
                bpy.ops.screen.animation_play()
                if self.timer is not None:
                    wm = context.window_manager
                    wm.event_timer_remove(self.timer)
                    del self.timer  # necessary ??
                self.handler_exists = True
            else:
                log.debug("Switching to static update")
                HandheldAnimate.status = "Running statically"
                if self.timer is None:
                    wm = context.window_manager
                    self.timer = wm.event_timer_add(1 / context.scene.render.fps, context.window)
                bpy.ops.screen.animation_play()
                bpy.app.handlers.frame_change_pre.remove(self.update_object_on_frame_changed)
                self.handler_exists = False

        if event.type == 'TIMER':
            HandheldAnimate.status = "Running statically"
            name = context.scene.handheld_data.selected_object
            self.update_object(
                bpy.data.objects[name],
                self.connection_thread.delta_loc,
                self.connection_thread.delta_rot)

        context.area.header_text_set(status_text)
        return {'PASS_THROUGH'}

    def execute(self, context):
        def acc_transform(acc):
            return [i / 16384 * 9.8 for i in acc]

        def rot_transform(rot):
            return [i / 131 for i in rot]

        def time_transform(t):
            return t / 1000

        HandheldAnimate.running = True
        self.connection_thread = HandheldClient(context, acc_transform, rot_transform, time_transform)
        self.connection_thread.start()

        # add timer for static updates:
        wm = context.window_manager
        self.timer = wm.event_timer_add(1 / context.scene.render.fps, context.window)

        # register operator as modal:
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self.handler_exists:
            bpy.ops.screen.animation_play()
            bpy.app.handlers.frame_change_pre.remove(self.update_object_on_frame_changed)
        else:
            wm = context.window_manager
            wm.event_timer_remove(self.timer)

        context.area.header_text_set()
        HandheldAnimate.status = "Connect"
        HandheldAnimate.running = False
        self.connection_thread.stop()

    def update_object(self, obj, delta_loc, delta_rot):
        loc = obj.location
        for i, xyz in enumerate(delta_loc):
            loc[i] += xyz

        rot = obj.rotation_euler
        for i, xyz in enumerate(delta_rot):
            rot[i] += radians(xyz)

    def update_object_on_frame_changed(self, scene):
        name = scene.handheld_data.selected_object
        obj = bpy.data.objects[name]
        try:
            self.update_object(obj, self.connection_thread.delta_loc, self.connection_thread.delta_rot)
        except:  # this function may be called when context becomes invalid. Nasty solution
            log.exception("On frame update:")
            bpy.app.handlers.frame_change_pre.pop()
        else:
            obj.keyframe_insert(data_path='location')
            obj.keyframe_insert(data_path='rotation_euler')


class ConnectionState(Enum):
    INIT = -1
    CONNECTING = 0
    SUCCESS = 1
    FAILED = 2
    CLOSED = 3
