cmake_minimum_required(VERSION 3.10)
project(RealTimeChess VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
if(MSVC)
    set(CMAKE_CXX_FLAGS "/W4")
    set(CMAKE_CXX_FLAGS_RELEASE "/O2")
else()
    set(CMAKE_CXX_FLAGS "-Wall -Wextra")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

# Find packages
find_package(OpenCV REQUIRED)

# Print OpenCV info
message(STATUS "OpenCV version: ${OpenCV_VERSION}")
message(STATUS "OpenCV include dirs: ${OpenCV_INCLUDE_DIRS}")

# Source files
file(GLOB_RECURSE MY_CPP_SOURCES
    "my_cpp/src/*.cpp"
    "my_cpp/src/*.hpp"
)

file(GLOB MY_CPP_PUB_SOURCES
    "my_cpp_pub/*.cpp"
    "my_cpp_pub/*.hpp"
)

set(ALL_SOURCES
    ${MY_CPP_SOURCES}
    ${MY_CPP_PUB_SOURCES}
)

# Include directories
include_directories(
    ${OpenCV_INCLUDE_DIRS}
    my_cpp/src
    my_cpp_pub
    my_cpp/openCV_451/include
)

# Create executable
add_executable(RealTimeChess ${ALL_SOURCES})

# Link libraries
target_link_libraries(RealTimeChess 
    ${OpenCV_LIBS}
)

# Set output directory
set_target_properties(RealTimeChess PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Copy resources to build directory
file(COPY pieces DESTINATION ${CMAKE_BINARY_DIR})
file(COPY pic DESTINATION ${CMAKE_BINARY_DIR})
file(COPY sounds DESTINATION ${CMAKE_BINARY_DIR})

# Print build info
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
