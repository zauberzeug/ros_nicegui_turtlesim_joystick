import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Twist

from nicegui import app, globals, run, ui
import threading
from pathlib import Path

class SimpleJoystick(Node):
    def __init__(self) -> None:
        super().__init__('joystick_node')
        self.publisher_ = self.create_publisher(Twist, 'turtle1/cmd_vel', 1)

        #this is where we add nicegui elements
        with globals.index_client:
            #create a row
            with ui.row().classes('items-stretch'):
                #create a card with the joystick in it
                with ui.card().classes('w-80 text-center items-center'):
                    # NOTE: Joystick will be reworked in the future, so this is a temporary workaround for the size.
                    ui.add_head_html('<style>.my-joystick > div { width: 20em !important; height: 20em !important; }</style>')
                    ui.joystick(
                        color='blue',
                        size=50,
                        #Note: x has to be inverted. Negative values turn the turtle to the right.
                        on_move=lambda e: self.publish_speeds(-e.x, e.y),
                        on_end=lambda _: self.publish_speeds(0.0, 0.0),
                    ).classes('my-joystick')
                    
                    ui.label('Publish steering commands by dragging your mouse around in the blue field').classes('mt-6')
                with ui.card().classes('w-44 text-center items-center'):
                    ui.label('Speeds').classes('text-2xl')
                    slider_props = 'readonly selection-color=transparent'

                    #create a slider & labelfor the linear speed
                    ui.label('linear velocity').classes('text-xs mb-[-1.8em]')
                    self.linear = ui.slider(min=-1, max=1, step=0.05, value=0).props(slider_props)
                    ui.label().bind_text_from(self.linear,'value', backward=lambda value: f'{value:.3f}')
                    
                    #create a slider & label for the angular speed
                    ui.label('angular velocity').classes('text-xs mb-[-1.8em]')
                    self.angular = ui.slider(min=-1, max=1, step=0.05, value=0).props(slider_props)
                    ui.label().bind_text_from(self.angular,'value', backward=lambda value: f'{value:.3f}')

    #this function publishes the twist message
    def publish_speeds(self, x:float, y:float) -> None:
        msg = Twist()
        self.get_logger().info('Publishing1-> linear: "%f", angular: "%f"' % (y, x))
        #this is for the sliders
        self.linear.value = y
        self.angular.value = x
        #loading values into the message
        msg.linear.x = y
        msg.angular.z = x 
        self.publisher_.publish(msg)

def ros_main() -> None:
    #Standart ROS2 node initialization
    print('Starting ROS2...', flush=True)

    rclpy.init()
    simple_joystick = SimpleJoystick()

    try:
        rclpy.spin(simple_joystick)
    except ExternalShutdownException:
        pass

def main():
    pass # NOTE: This is originally used as the ROS entry point, but we give the control of the node to NiceGUI.


#Starting the ros node in a thread managed by nicegui. It will restarted with "on_startup" after a reload.
#It has to be in a thread, since NiceGUI wants the main thread for itself.
app.on_startup(lambda: threading.Thread(target=ros_main).start())

#This is for the automatic reloading by nicegui/fastapi
run.APP_IMPORT_STRING = f'{__name__}:app'

#We add reload dirs to just watch changes in our package
ui.run(title='Turtlesim Joystick',uvicorn_reload_dirs=str(Path(__file__).parent.resolve()))