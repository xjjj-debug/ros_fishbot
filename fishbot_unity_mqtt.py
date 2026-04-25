import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import paho.mqtt.client as mqtt
import json
import threading

# MQTT配置（根据你的环境修改IP和端口）
MQTT_BROKER = "192.168.1.100"  # 运行MQTT服务器的IP
MQTT_PORT = 1883
MQTT_TOPIC_PUB = "fishbot/odom"  # 发布小车坐标
MQTT_TOPIC_SUB = "fishbot/cmd"   # 订阅Unity控制指令

class FishBotUnityMQTT(Node):
    def __init__(self):
        super().__init__('fishbot_unity_mqtt')
        # 1. 订阅ROS2小车里程计话题
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',  # 鱼香小车默认里程计话题
            self.odom_callback,
            10
        )
        
        # 2. 初始化MQTT客户端
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # 启动MQTT循环线程
        self.mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever)
        self.mqtt_thread.daemon = True
        self.mqtt_thread.start()
        
        self.get_logger().info("ROS2 <-> Unity MQTT 节点启动成功！")

    # MQTT连接回调
    def on_mqtt_connect(self, client, userdata, flags, rc):
        self.get_logger().info(f"MQTT连接成功，状态码：{rc}")
        # 订阅Unity下发的控制话题
        self.mqtt_client.subscribe(MQTT_TOPIC_SUB)

    # 接收Unity3D控制指令回调
    def on_mqtt_message(self, client, userdata, msg):
        cmd_data = json.loads(msg.payload.decode())
        linear_x = cmd_data.get("linear_x", 0.0)
        angular_z = cmd_data.get("angular_z", 0.0)
        self.get_logger().info(f"接收Unity控制：线速度={linear_x}，角速度={angular_z}")
        # 此处可添加代码，将控制指令转发给小车电机

    # 里程计数据回调：发送坐标给Unity
    def odom_callback(self, msg):
        # 提取小车坐标和朝向
        pose = {
            "x": msg.pose.pose.position.x,
            "y": msg.pose.pose.position.y,
            "yaw": self.get_yaw_from_quaternion(
                msg.pose.pose.orientation.x,
                msg.pose.pose.orientation.y,
                msg.pose.pose.orientation.z,
                msg.pose.pose.orientation.w
            )
        }
        # 发布MQTT消息
        self.mqtt_client.publish(MQTT_TOPIC_PUB, json.dumps(pose))

    # 四元数转欧拉角（获取小车朝向yaw）
    def get_yaw_from_quaternion(self, x, y, z, w):
        import math
        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(t3, t4)

def main(args=None):
    rclpy.init(args=args)
    node = FishBotUnityMQTT()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
