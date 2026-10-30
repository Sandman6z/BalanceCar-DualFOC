#pragma once
#include <stdint.h>
typedef struct {
    float ia, ib, angle, target, d_integral, q_integral;
    float u, v, w, kp, ki;
} Motor;
extern volatile Motor motors[2];
void current_step(volatile Motor *m, float bus, float dt);
float attitude_step(float gyro, float accel_angle, float dt);
