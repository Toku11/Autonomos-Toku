#include "ros/ros.h"
#include "sensor_msgs/LaserScan.h"
#include <std_msgs/Int16.h>
#include <std_msgs/String.h>
#include <geometry_msgs/Twist.h>

//parameters
#include <ros/ros.h>

class auto_stop
{
public:
	auto_stop(ros::NodeHandle nh)
	{
		n_.param<int>("angle_front", angle_front, 40);
		n_.param<int>("angle_back", angle_back, 40);
		n_.param<float>("break_distance", break_distance, 0.45);
		pubEmergencyStop_=nh.advertise<std_msgs::Int16>(nh.resolveName("manual_control/speed"), 1);
		subScan_ = n_.subscribe("scan", 1, &auto_stop::scanCallback,this);
		subTwist_ = n_.subscribe("motor_control/twist",1,&auto_stop::speedCallback,this); 
	}
	~auto_stop(){}

    void speedCallback(const geometry_msgs::Twist& twist)
	{
		direction=twist.linear.x;
	}

	void scanCallback(const sensor_msgs::LaserScan::ConstPtr& scan)
	{
	    int count = scan->scan_time / scan->time_increment;
	    float  break_distance_=break_distance;
	    if (abs(direction)>500)
	    	break_distance_=(abs(direction)/500)*break_distance;
	    std_msgs::Int16 speed;
	    speed.data=0;
	    //ROS_INFO("speed %f",break_distance_);	
		if(direction < 0){	//backw.
			for(int i = 0; i < (angle_back/2)+1; i++){
				if (scan->ranges[i] <= break_distance_){
				
					pubEmergencyStop_.publish(speed);
					//ROS_INFO("Obstacle");
					return;
			    }
			}
			for(int k = (360-(angle_back/2)); k < count; k++){
				if (scan->ranges[k] <= break_distance_){
					pubEmergencyStop_.publish(speed);
					return;
			    }
			}
		}

		if(direction > 0){ //forw.
			for(int j = (180-(angle_front/2)); j < (180+(angle_front/2))+1; j++){
				if (scan->ranges[j] <= break_distance_){
					pubEmergencyStop_.publish(speed);
					return;
			    }
			}
		}
	}

	private:
	  	int angle_front;
		int angle_back;
		float break_distance;
		int direction;
	  	ros::NodeHandle n_; 
	  	ros::Publisher pubEmergencyStop_;
	  	ros::Subscriber subScan_;
	  	ros::Subscriber subTwist_;

};//End of class auto_stop



int main(int argc, char **argv)
{
    ros::init(argc, argv, "move_lights_node");
    ros::NodeHandle nh; 
    //auto_stop autoStopObject(nh);
	
    ros::Publisher light_publisher;
    light_publisher=nh.advertise<std_msgs::String>(nh.resolveName("manual_control/lights"), 1);

    std_msgs::String light_command;

    ros::Publisher steering_publisher;
    steering_publisher=nh.advertise<std_msgs::Int16>(nh.resolveName("manual_control/steering"), 1);
    std_msgs::Int16 steering_command;

    ros::Rate loop_rate(1);

    ROS_INFO("Hola cochesito chingon!");
	int i=0;
	while(ros::ok())
	{
		switch (i){
		case 0:
			light_command.data="le";
			steering_command.data=0;
			ROS_INFO("left");
			//light_publisher.publish(light_command);
			steering_publisher.publish(steering_command);
                      i=1;
		break;

		case 1:
			light_command.data="fr";
			steering_command.data=90;
			ROS_INFO("front");
			//light_publisher.publish(light_command);
			steering_publisher.publish(steering_command);
                      i=2;
		break;


		case 2:
			light_command.data="ri";
			steering_command.data=180;
			ROS_INFO("right");
			//light_publisher.publish(light_command);
			steering_publisher.publish(steering_command);
                      i=0;
		break;
                }
		//ros::spin();
		ros::spinOnce();
	        loop_rate.sleep();
	}
    return 0;
}
