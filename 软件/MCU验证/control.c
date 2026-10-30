#include "control.h"
#include <math.h>
volatile Motor motors[2];
static float angle;
static float clamp(float x, float limit) { return fminf(limit, fmaxf(-limit, x)); }
void current_step(volatile Motor *m, float bus, float dt) {
    float s = sinf(m->angle), c = cosf(m->angle);
    float alpha = m->ia, beta = (m->ia + 2.0f * m->ib) * 0.577350269f;
    float id = alpha * c + beta * s, iq = -alpha * s + beta * c;
    float limit = fmaxf(bus, 0.0f) * 0.45f;
    float ed = -id, eq = m->target - iq;
    m->d_integral = clamp(m->d_integral + m->ki * ed * dt, limit);
    m->q_integral = clamp(m->q_integral + m->ki * eq * dt, limit);
    float vd = clamp(m->kp * ed + m->d_integral, limit);
    float vq = clamp(m->kp * eq + m->q_integral, limit);
    float a = vd * c - vq * s, b = vd * s + vq * c;
    float u = a, v = -0.5f * a + 0.866025404f * b, w = -0.5f * a - 0.866025404f * b;
    float common = -0.5f * (fmaxf(u, fmaxf(v, w)) + fminf(u, fminf(v, w)));
    float scale = bus > 1.0f ? 1.0f / bus : 0.0f;
    m->u = 0.5f + clamp((u + common) * scale, 0.42f);
    m->v = 0.5f + clamp((v + common) * scale, 0.42f);
    m->w = 0.5f + clamp((w + common) * scale, 0.42f);
}
float attitude_step(float gyro, float accel_angle, float dt) {
    angle = 0.98f * (angle + gyro * dt) + 0.02f * accel_angle;
    return angle;
}
