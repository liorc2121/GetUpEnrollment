import os

from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
import datetime
import ctypes
import _ctypes
import pygame
import sys
import time
import cx_Freeze
from tkinter import Tk, filedialog

if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# colors for drawing different bodies
SKELETON_COLORS = [pygame.color.THECOLORS["red"],
                   pygame.color.THECOLORS["blue"],
                   pygame.color.THECOLORS["green"],
                   pygame.color.THECOLORS["orange"],
                   pygame.color.THECOLORS["purple"],
                   pygame.color.THECOLORS["yellow"],
                   pygame.color.THECOLORS["violet"]]

dic_name_to_index = {0: 'SpineBase',
                     1: 'SpineMid',
                     2: 'Neck',
                     3: 'Head',
                     4: 'ShoulderLeft',
                     5: 'ElbowLeft',
                     6: 'WristLeft',
                     7: 'HandLeft',
                     8: 'ShoulderRight',
                     9: 'ElbowRight',
                     10: 'WristRight',
                     11: 'HandRight',
                     12: 'HipLeft',
                     13: 'KneeLeft',
                     14: 'AnkleLeft',
                     15: 'FootLeft',
                     16: 'HipRight',
                     17: 'KneeRight',
                     18: 'AnkleRight',
                     19: 'FootRight',
                     20: 'SpineShoulder',
                     21: 'HandTipLeft',
                     22: 'ThumbLeft',
                     23: 'HandTipRight',
                     24: 'ThumbRight'}


class Point:
    def __init__(self, point_name, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.name = point_name


class BodyGameRuntime(object):
    def __init__(self):
        pygame.init()

        # Used to manage how fast the screen updates
        self._clock = pygame.time.Clock()
        self._saveMode = False
        # Set the width and height of the screen [width, height]
        self._infoObject = pygame.display.Info()
        self._screen = pygame.display.set_mode(
            ((self._infoObject.current_w >> 1), (self._infoObject.current_h >> 1) + 200),
            pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE, 32)

        self.recordCount = 0
        self.subDirectory = None
        self.is_saving_pictures = False
        self.is_saving_points = False
        self.value = None
        self.DIRECTORY = 'C:\\Recordings'

        pygame.display.set_caption("Kinect for Windows v2 Body Game")

        # Loop until the user clicks the close button.
        self._done = False

        # Used to manage how fast the screen updates
        self._clock = pygame.time.Clock()

        # Kinect runtime object, we want only color and body frames
        self._kinect = PyKinectRuntime.PyKinectRuntime(
            PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_Depth)

        # back buffer surface for getting Kinect color frames, 32bit color, width and height equal to the Kinect color frame size
        self._frame_surface = pygame.Surface(
            (self._kinect.color_frame_desc.Width, self._kinect.color_frame_desc.Height), 0, 32)

        # here we will store skeleton data 
        self._bodies = None

    def draw_body_bone(self, joints, jointPoints, color, joint0, joint1):
        joint0State = joints[joint0].TrackingState;
        joint1State = joints[joint1].TrackingState;

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked) or (joint1State == PyKinectV2.TrackingState_NotTracked):
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred) and (joint1State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good 
        start = (jointPoints[joint0].x, jointPoints[joint0].y)
        end = (jointPoints[joint1].x, jointPoints[joint1].y)

        try:
            pygame.draw.line(self._frame_surface, color, start, end, 8)
        except:  # need to catch it due to possible invalid positions (with inf)
            pass

    def draw_body(self, joints, jointPoints, color):
        # Torso
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Head, PyKinectV2.JointType_Neck);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Neck, PyKinectV2.JointType_SpineShoulder);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_SpineMid);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineMid, PyKinectV2.JointType_SpineBase);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_ShoulderRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_ShoulderLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipLeft);

        # Right Arm    
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderRight,
                            PyKinectV2.JointType_ElbowRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowRight,
                            PyKinectV2.JointType_WristRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight,
                            PyKinectV2.JointType_HandRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandRight,
                            PyKinectV2.JointType_HandTipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight,
                            PyKinectV2.JointType_ThumbRight);

        # Left Arm
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderLeft,
                            PyKinectV2.JointType_ElbowLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowLeft, PyKinectV2.JointType_WristLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_HandLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandLeft,
                            PyKinectV2.JointType_HandTipLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_ThumbLeft);

        # Right Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipRight, PyKinectV2.JointType_KneeRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeRight,
                            PyKinectV2.JointType_AnkleRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleRight,
                            PyKinectV2.JointType_FootRight);

        # Left Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipLeft, PyKinectV2.JointType_KneeLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeLeft, PyKinectV2.JointType_AnkleLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleLeft, PyKinectV2.JointType_FootLeft);

    def draw_color_frame(self, frame, target_surface):
        target_surface.lock()
        address = self._kinect.surface_as_array(target_surface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        target_surface.unlock()

    def button_save(self, x, y, width, height, active_color, inactive_color, message='save', click_action=None):
        mouse = pygame.mouse.get_pos()
        click_event = pygame.mouse.get_pressed()
        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            pygame.draw.rect(self._screen, active_color, (x, y, width, height))

            if click_event[0] == 1 and click_action != None:
                click_action()
        else:
            pygame.draw.rect(self._screen, inactive_color, (x, y, width, height))

        btn_font_size = pygame.font.Font("freesansbold.ttf", 20)
        btn_msg_surface = btn_font_size.render(message, True, (255, 255, 255))
        btn_msg_rect = btn_msg_surface.get_rect()
        btn_msg_rect.center = ((x + (width / 2)), (y + (height / 2)))
        self._screen.blit(btn_msg_surface, btn_msg_rect)

    def save_pos(self):
        self._saveMode = not self._saveMode

        if (self._saveMode):
            self.recordCount = 0
            self.subDirectory = 'Record ' + str(datetime.datetime.now()).replace('.', ':').replace(':', '-')

        time.sleep(0.2)

    def save_frame(self, frame, directory):
        out_file = directory + self.subDirectory + '\\Frames' + '\\Record' + str(self.recordCount) + '.jpeg'
        dir_path = os.path.dirname(out_file)
        if dir_path != '' and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        pygame.image.save(frame, out_file)

    def save_bodies_coordinate(self, depth_frame, directory):
        bodies_points = {}
        for i in range(0, self._kinect.max_body_count):
            body = self._bodies.bodies[i]
            if not body.is_tracked:
                continue

            list_points = self.save_body_coordinate(body.joints,
                                                    self._kinect.body_joints_to_depth_space(body.joints),
                                                    depth_frame)
            bodies_points[i] = list_points

        out_file = directory + self.subDirectory + '\\Points' + '\\Points' + str(self.recordCount) + '.txt'
        dir_path = os.path.dirname(out_file)
        if dir_path != '' and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if len(bodies_points) > 0 and bodies_points != {}:
            with open(out_file, 'w') as file:
                for body_index in bodies_points:
                    file.write('body ' + str(body_index) + os.linesep)
                    for point in bodies_points[body_index]:
                        file.write(str(point.x) + '#' +
                                   str(point.y) + '#' +
                                   str(point.z) + '#' +
                                   str(point.name) +
                                   os.linesep)

                file.close()

    def save_body_coordinate(self, joints, jointsPoints, depth_frame):

        list = []

        for place in range(JointType_Count):
            joint0State = joints[place].TrackingState;

            # both joints are not tracked
            if (joint0State == PyKinectV2.TrackingState_NotTracked) or (
                    joint0State == PyKinectV2.TrackingState_Inferred):
                continue

            point = Point(dic_name_to_index[place],
                          int(jointsPoints[place].x),
                          int(jointsPoints[place].y),
                          int(depth_frame[int(jointsPoints[place].y) * 512 + int(jointsPoints[place].x)]))

            list.append(point)

        return list

    def check_box(self, x, y, width, height, active_color, inactive_color, message, active, click_action=None):
        mouse = pygame.mouse.get_pos()
        click_event = pygame.mouse.get_pressed()

        if active:
            if x + width > mouse[0] > x and y + height > mouse[1] > y:
                pygame.draw.rect(self._screen, active_color, (x, y, width + 2, height + 2))

                if click_event[0] == 1 and click_action != None:
                    click_action()
            else:
                pygame.draw.rect(self._screen, inactive_color, (x, y, width + 2, height + 2))
        else:
            pygame.draw.rect(self._screen, (0, 0, 0), (x, y, width + 2, height + 2))

            if x + width > mouse[0] > x and y + height > mouse[1] > y:
                pygame.draw.rect(self._screen, active_color, (x, y, width, height), 2)

                if click_event[0] == 1 and click_action != None:
                    click_action()
            else:
                pygame.draw.rect(self._screen, inactive_color, (x, y, width, height), 2)

        btn_font_size = pygame.font.Font("freesansbold.ttf", 25)
        btn_msg_surface = btn_font_size.render(message, True, (200, 200, 200))
        btn_msg_rect = btn_msg_surface.get_rect()
        btn_msg_rect.topleft = (x + width + 10, y)
        self._screen.blit(btn_msg_surface, btn_msg_rect)

    def change_check_box_save_pictures(self):
        self.is_saving_pictures = not self.is_saving_pictures
        time.sleep(0.2)

    def change_check_box_save_points(self):
        self.is_saving_points = not self.is_saving_points
        time.sleep(0.2)

    def radio_button(self, x, y, width, height, active_color, inactive_color, message, active, value,
                     click_action=None):
        mouse = pygame.mouse.get_pos()
        click_event = pygame.mouse.get_pressed()

        if active:
            if x + width > mouse[0] > x and y + height > mouse[1] > y:
                pygame.draw.rect(self._screen, active_color, (x, y, width + 2, height + 2))

                if click_event[0] == 1 and click_action != None:
                    value = None
                    click_action(value)
            else:
                pygame.draw.rect(self._screen, inactive_color, (x, y, width + 2, height + 2))
        else:
            pygame.draw.rect(self._screen, (0, 0, 0), (x, y, width + 2, height + 2))

            if x + width > mouse[0] > x and y + height > mouse[1] > y:
                pygame.draw.rect(self._screen, active_color, (x, y, width, height), 2)

                if click_event[0] == 1 and click_action != None:
                    click_action(value)
            else:
                pygame.draw.rect(self._screen, inactive_color, (x, y, width, height), 2)

        btn_font_size = pygame.font.Font("freesansbold.ttf", 20)
        btn_msg_surface = btn_font_size.render(message, True, (200, 200, 200))
        btn_msg_rect = btn_msg_surface.get_rect()
        btn_msg_rect.topleft = (x + width + 10, y)
        self._screen.blit(btn_msg_surface, btn_msg_rect)

    def change_radio_button_value(self, value):
        self.value = value
        time.sleep(0.13)

    def select_folder(self):
        root = Tk()
        root.title("select folder")
        root.winfo_toplevel()
        root.iconify()
        filename = filedialog.askdirectory()
        if filename is not '' and filename is not None:
            self.DIRECTORY = filename
        print(filename)
        root.destroy()

    def set_radio_buttons(self, y):
        self.radio_button(10,
                          y,
                          10,
                          10,
                          pygame.color.THECOLORS["red"],
                          pygame.color.THECOLORS["orange"],
                          '4.no problem',
                          self.value == 4,
                          4,
                          self.change_radio_button_value)

        self.radio_button(170,
                          y,
                          10,
                          10,
                          pygame.color.THECOLORS["red"],
                          pygame.color.THECOLORS["orange"],
                          '3.arm use',
                          self.value == 3,
                          3,
                          self.change_radio_button_value)

        self.radio_button(310,
                          y,
                          10,
                          10,
                          pygame.color.THECOLORS["red"],
                          pygame.color.THECOLORS["orange"],
                          '2.critcal arm use',
                          self.value == 2,
                          2,
                          self.change_radio_button_value)

        self.radio_button(520,
                          y,
                          10,
                          10,
                          pygame.color.THECOLORS["red"],
                          pygame.color.THECOLORS["orange"],
                          '1. minor aid',
                          self.value == 1,
                          1,
                          self.change_radio_button_value)

        self.radio_button(700,
                          y,
                          10,
                          10,
                          pygame.color.THECOLORS["red"],
                          pygame.color.THECOLORS["orange"],
                          '0.major aid',
                          self.value == 0,
                          0,
                          self.change_radio_button_value)

    def set_check_boxes(self, x, y, width, height):
        self.check_box(x,
                       y,
                       width,
                       height,
                       pygame.color.THECOLORS["red"],
                       pygame.color.THECOLORS["orange"],
                       'save pictures',
                       self.is_saving_pictures,
                       self.change_check_box_save_pictures)

        self.check_box(x + 25 + 190 + 10,
                       y,
                       width,
                       height,
                       pygame.color.THECOLORS["red"],
                       pygame.color.THECOLORS["orange"],
                       'save points',
                       self.is_saving_points,
                       self.change_check_box_save_points)

    def dir_frame(self, x, y, width, height, active_color, inactive_color):
        mouse = pygame.mouse.get_pos()
        click_event = pygame.mouse.get_pressed()
        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            pygame.draw.rect(self._screen, active_color, (x, y, width, height), 2)

            if click_event[0] == 1:
                self.select_folder()
        else:
            pygame.draw.rect(self._screen, inactive_color, (x, y, width, height))

        btn_font_size = pygame.font.Font("freesansbold.ttf", 14)
        btn_msg_surface = btn_font_size.render(self.DIRECTORY, True, (255, 255, 255))
        btn_msg_rect = btn_msg_surface.get_rect()
        btn_msg_rect.center = ((x + (width / 2)), (y + (height / 2)))
        self._screen.blit(btn_msg_surface, btn_msg_rect)

    def run(self):
        # -------- Main Program Loop -----------
        while not self._done:
            # --- Main event loop
            for event in pygame.event.get():  # User did something
                if event.type == pygame.QUIT:  # If user clicked close
                    self._done = True  # Flag that we are done so we exit this loop

                elif event.type == pygame.VIDEORESIZE:  # window resized
                    self._screen = pygame.display.set_mode(event.dict['size'],
                                                           pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE, 32)

            # --- Game logic should go here

            # --- Getting frames and drawing  
            # --- Woohoo! We've got a color frame! Let's fill out back buffer surface with frame's data 
            if self._kinect.has_new_color_frame():
                frame = self._kinect.get_last_color_frame()
                self.draw_color_frame(frame, self._frame_surface)
                frame = None

            # --- Cool! We have a body frame, so can get skeletons
            if self._kinect.has_new_body_frame():
                self._bodies = self._kinect.get_last_body_frame()

            if self._kinect.has_new_depth_frame():
                lior = 'Happy'

            # --- draw skeletons to _frame_surface
            if self._bodies is not None:
                for i in range(0, self._kinect.max_body_count):
                    body = self._bodies.bodies[i]
                    if not body.is_tracked:
                        continue

                    joints = body.joints
                    # convert joint coordinates to color space 
                    joint_points = self._kinect.body_joints_to_color_space(joints)
                    self.draw_body(joints, joint_points, SKELETON_COLORS[i])
            # --- copy back buffer surface pixels to the screen, resize it if needed and keep aspect ratio
            # --- (screen size may be different from Kinect's color frame size)
            h_to_w = float(self._frame_surface.get_height()) / self._frame_surface.get_width()
            target_height = int(h_to_w * self._screen.get_width())
            surface_to_draw = pygame.transform.scale(self._frame_surface, (self._screen.get_width(), target_height));
            self._screen.blit(surface_to_draw, (0, 0))

            btn_size_height = 50
            btn_size_width = 100
            btn_save_loc_x = 20
            btn_save_loc_y = self._screen.get_height() - 3 * btn_size_height / 2
            msg = 'save' if not self._saveMode else 'stop'

            self.button_save(btn_save_loc_x,
                             btn_save_loc_y,
                             btn_size_width,
                             btn_size_height,
                             pygame.color.THECOLORS["red"],
                             pygame.color.THECOLORS["orange"],
                             msg,
                             self.save_pos)

            cb_save_pic_loc_x = btn_save_loc_x + btn_size_width + 5
            cb_save_pic_loc_y = btn_save_loc_y
            cb_size_height = 25
            cb_size_width = 25

            self.set_check_boxes(cb_save_pic_loc_x + 20, cb_save_pic_loc_y + btn_size_height / 2, cb_size_height,
                                 cb_size_width)

            self.set_radio_buttons(cb_save_pic_loc_y - 50)

            self.dir_frame(cb_save_pic_loc_x + 430, cb_save_pic_loc_y, 400, btn_size_height,
                           pygame.color.THECOLORS["red"],
                           pygame.color.THECOLORS["orange"])

            if self._saveMode:
                pygame.draw.circle(self._screen, pygame.color.THECOLORS["red"], [10, 10], 10)
                directory = self.DIRECTORY + '\\'

                if self.value is not None:
                    directory = self.DIRECTORY + '\\' + str(self.value) + '\\'
                if self.is_saving_pictures:
                    self.save_frame(
                        pygame.transform.scale(self._frame_surface, (self._screen.get_width(), target_height)),
                        directory)

                if self.is_saving_points:
                    self.save_bodies_coordinate(self._kinect.get_last_depth_frame(), directory)

                self.recordCount += 1

            pygame.display.update()

            # --- Go ahead and update the screen with what we've85 drawn.
            pygame.display.flip()

            # --- Limit to 60 frames per second
            self._clock.tick(60)

        # Close our Kinect sensor, close the window and quit.
        self._kinect.close()
        pygame.quit()


__main__ = "Kinect v2 Body Game"
game = BodyGameRuntime();
game.run();
