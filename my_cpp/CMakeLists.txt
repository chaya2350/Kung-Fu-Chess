cmake_minimum_required(VERSION 3.16)
project(KungFuChess)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)




# Collect all .cpp and .hpp files in src and my_cpp_pub
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.hpp" "../my_cpp_pub/*.cpp" "../my_cpp_pub/*.hpp")




add_executable(${PROJECT_NAME} ${SOURCES})

set(OPENCV_DIR "${CMAKE_CURRENT_SOURCE_DIR}/openCV_451")
set(OPENCV_INCLUDE_DIR "${OPENCV_DIR}/include")
set(OPENCV_LIB_DIR "${OPENCV_DIR}/bin")

target_include_directories(${PROJECT_NAME} PRIVATE
    ${OPENCV_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/json
    ${CMAKE_CURRENT_SOURCE_DIR}/../my_cpp_pub
)



target_link_directories(${PROJECT_NAME} PRIVATE ${OPENCV_LIB_DIR})
target_link_directories(${PROJECT_NAME} PRIVATE "C:/Libs/SDL2/lib/x64")
target_include_directories(${PROJECT_NAME} PRIVATE "C:/Libs/SDL2/include")

target_link_libraries(${PROJECT_NAME}
    $<$<CONFIG:Debug>:${OPENCV_LIB_DIR}/opencv_world451d.lib>
    $<$<CONFIG:Release>:${OPENCV_LIB_DIR}/opencv_world451.lib>
    SDL2.lib SDL2main.lib SDL2_mixer.lib
)

if(WIN32)
    add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<$<CONFIG:Debug>:${OPENCV_LIB_DIR}/opencv_world451d.dll>"
        "$<$<CONFIG:Release>:${OPENCV_LIB_DIR}/opencv_world451.dll>"
        $<TARGET_FILE_DIR:${PROJECT_NAME}>
    )
endif()

message(STATUS "SOURCES: ${SOURCES}")
message(STATUS "OpenCV: ${OPENCV_DIR}")