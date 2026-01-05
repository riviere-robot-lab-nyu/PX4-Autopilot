import rclpy
from rclpy.node import Node
from px4_msgs.msg import ActuatorMotors, OffboardControlMode, VehicleCommand, VehicleStatus
import time

class ThrusterDirectControl(Node):
    def __init__(self):
        super().__init__('thruster_direct_control')

        # Publishers
        self.actuator_pub = self.create_publisher(ActuatorMotors, '/fmu/in/actuator_motors', 10)
        self.offboard_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', 10)
        self.vehicle_command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', 10)

        # Timer (Must send at > 2Hz or failsafe triggers)
        self.timer = self.create_timer(0.1, self.timer_callback) # 10Hz

        self.count = 0
        self.get_logger().info("Starting Thruster Control Node...")

    def arm_vehicle(self):
        # Send Arm Command
        cmd = VehicleCommand()
        cmd.command = VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM
        cmd.param1 = 1.0 # 1 = Arm
        cmd.target_system = 1
        cmd.target_component = 1
        cmd.source_system = 1
        cmd.source_component = 1
        cmd.from_external = True
        self.vehicle_command_pub.publish(cmd)

    def timer_callback(self):
        # 1. Publish Offboard Control Mode (Heartbeat)
        # We tell PX4: "We want to control actuators directly"
        offboard_msg = OffboardControlMode()
        offboard_msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        offboard_msg.position = False
        offboard_msg.velocity = False
        offboard_msg.acceleration = False
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.direct_actuator = True # <--- CRITICAL
        self.offboard_pub.publish(offboard_msg)

        # 2. Switch to Offboard Mode & Arm (Only do this once after a few heartbeats)
        if self.count == 10:
            self.evaluate_mode_switch()
            self.arm_vehicle()

        # 3. Send Motor Command
        motors_msg = ActuatorMotors()
        motors_msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)

        # The array has 12 slots. Initialize all to NaN (ignore)
        motors_msg.control = [float('nan')] * 12

        # Set Motor 1 (Index 0) to 30% Forward
        # Range is -1.0 to 1.0
        motors_msg.control[0] = 0.3

        self.actuator_pub.publish(motors_msg)
        self.count += 1

    def evaluate_mode_switch(self):
        # Command to switch to Offboard Mode
        cmd = VehicleCommand()
        cmd.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        cmd.param1 = 1.0 # Custom mode
        cmd.param2 = 6.0 # Offboard mode
        cmd.target_system = 1
        cmd.target_component = 1
        cmd.source_system = 1
        cmd.source_component = 1
        cmd.from_external = True
        self.vehicle_command_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = ThrusterDirectControl()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
