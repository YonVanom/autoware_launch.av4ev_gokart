cmake_minimum_required(VERSION 3.14)
project(offroad_launch_minimal)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config rviz DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/sim_control_mode_publisher.py DESTINATION lib/${PROJECT_NAME})

ament_package()
