#include <heading/heading.h>
#include <tf/transform_broadcaster.h>


int contador=0;
float yaw=0,offset=0,ang=0, noffset=0, offset2=0;
bool bandera=false, inicial=false;

heading::heading(ros::NodeHandle nh) : nh_(nh), priv_nh_("~"), my_serial("/dev/ttyUSB0",115200, serial::Timeout::simpleTimeout(1000))
{
  result="";
  priv_nh_.param<std::string>("arduino_serial_port", serial_port_, "/dev/ttyUSB0");
  priv_nh_.param("arduino_baud_rate", baud_rate_,115200);
  my_serial.close();
  my_serial.setPort(serial_port_);
  my_serial.setBaudrate(baud_rate_);
  my_serial.open();
  //my_serial.setTimeout(1000);
  //my_serial.Timeout.simpleTimeout(1000)
  //odometry_sub = nh_.subscribe("visual_odometry",1,&heading::ReceiveOdometry,this);
  odometry_sub = nh_.subscribe("/odom",1,&heading::ReceiveOdometry,this);
  pub_yaw_=nh_.advertise<std_msgs::Float32>(nh_.resolveName("model_car/yaw"), 1);
  init();
  
}
    //! Empty stub
heading::~heading() {}
void heading::init()
{
    try
    {
      ROS_INFO("heading::Is the serial port %s open?",serial_port_.c_str());
      //cout << my_serial.getBaudrate() << endl;
    if(my_serial.isOpen())
      ROS_INFO("heading:: Yes.");
    else
      ROS_INFO("heading:: No.");
    }
    catch(const std::exception& e)
    {  
        ROS_ERROR("heading:: could not find serial port");
    }
}

void heading::ReceiveOdometry(const nav_msgs::Odometry::ConstPtr& msg){
         //yaw=msg->pose.pose.position.z;
  //if (bandera==false){
  yaw=msg->twist.twist.angular.x;//thcamara
  if(contador<400){
	    offset=yaw+offset;
	    contador++;
  }else{
		offset=offset/contador;
		odometry_sub.shutdown();
		bandera=true;}
  //}//else{
    //noffset=msg->twist.twist.angular.y;
    
  //}

}
void heading::getHeading()
{
  try
  {
    std::string begin = my_serial.read(4); //yrp string
    if (begin.find("ypr")!=std::string::npos)
    {
      result = my_serial.readline();//read(7);//yaw data
      my_serial.flushInput();
      //result = my_serial.read(7);//yaw data
      //my_serial.flushInput();
      std::stringstream ss(result);
      
      std_msgs::Float32 angle;
      ss>>ang;


  if (bandera==true){
		//ROS_INFO("actualizado");
	if (inicial==false){
        		offset=offset+ang;
			inicial=true;}
	ang=ang-offset-noffset;
	if (ang>180){
		ang=ang-360;
	}
	else if (ang<-180){
		ang=ang+360;
	}	
	}
      angle.data=-ang; //string to double
      pub_yaw_.publish(angle);
    }
    //std::string end=my_serial.readline(); //rest data
    //ROS_INFO("readline:%s \n",result.c_str());
 
    //return angle.data; 
    //return =atof(str_quan.c_str());
  }
  catch(const std::exception& e)
  {  
    ROS_ERROR("heading:: could not find serial port");
  }
}
