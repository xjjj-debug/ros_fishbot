using UnityEngine;
using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;
using System;
using System.Text;

public class FishBotUnitySync : MonoBehaviour
{
    [Header("MQTT配置")]
    public string mqttBroker = "192.168.1.100";
    public int mqttPort = 1883;
    private MqttClient mqttClient;

    [Header("小车虚拟模型")]
    public GameObject fishBotModel;

    // 话题定义（与ROS2端保持一致）
    private readonly string topicOdom = "fishbot/odom";
    private readonly string topicCmd = "fishbot/cmd";

    void Start()
    {
        // 连接MQTT服务器
        mqttClient = new MqttClient(mqttBroker);
        mqttClient.MqttMsgPublishReceived += OnOdomReceived;
        
        string clientId = "UnityClient_" + Guid.NewGuid();
        mqttClient.Connect(clientId);
        
        // 订阅小车坐标话题
        mqttClient.Subscribe(new string[] { topicOdom }, new byte[] { MqttMsgBase.QOS_LEVEL_AT_MOST_ONCE });
        Debug.Log("Unity 已连接MQTT，等待小车数据...");
    }

    // 接收ROS2小车坐标，更新虚拟模型
    void OnOdomReceived(object sender, MqttMsgPublishEventArgs e)
    {
        try
        {
            string json = Encoding.UTF8.GetString(e.Message);
            BotPose pose = JsonUtility.FromJson<BotPose>(json);
            
            // Unity坐标系转换（根据你的场景调整）
            Vector3 targetPos = new Vector3(pose.x, 0, pose.y);
            Quaternion targetRot = Quaternion.Euler(0, -pose.yaw * Mathf.Rad2Deg, 0);
            
            // 实时更新模型位置和旋转
            fishBotModel.transform.position = targetPos;
            fishBotModel.transform.rotation = targetRot;
        }
        catch (Exception ex)
        {
            Debug.LogError("数据解析失败：" + ex.Message);
        }
    }

    // 发送控制指令给ROS2小车（可绑定按钮/键盘事件）
    public void SendBotCommand(float linearX, float angularZ)
    {
        BotCmd cmd = new BotCmd { linear_x = linearX, angular_z = angularZ };
        string json = JsonUtility.ToJson(cmd);
        mqttClient.Publish(topicCmd, Encoding.UTF8.GetBytes(json));
    }

    // 数据结构：小车位姿
    [Serializable]
    public class BotPose
    {
        public float x;
        public float y;
        public float yaw;
    }

    // 数据结构：小车控制指令
    [Serializable]
    public class BotCmd
    {
        public float linear_x;
        public float angular_z;
    }

    void OnDestroy()
    {
        if (mqttClient != null && mqttClient.IsConnected)
            mqttClient.Disconnect();
    }
}
