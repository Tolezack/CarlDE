#pragma once
// Stable C ABI for hot-swappable gameplay modules. Do NOT pass C++ World objects.
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define BRAINROT_LIVE_ABI 1u
typedef struct BrainrotLiveAPI {
    uint32_t abi_version;
    void* userdata;
    uint8_t (*get_block)(void* userdata,int x,int y,int z);
    int (*set_block)(void* userdata,int x,int y,int z,uint8_t block);
} BrainrotLiveAPI;
// Plugin must export both: uint32_t brainrot_live_version(void);
// void brainrot_live_tick(const BrainrotLiveAPI *api,double dt);
#ifdef __cplusplus
}
#endif
