#include "brainrot_live_api.h"
// EDIT WHILE GAME IS RUNNING and execute tools/rebuild_live.sh.
// The executable swaps the newly built library at the next frame.
extern "C" uint32_t brainrot_live_version() {return BRAINROT_LIVE_ABI;}
extern "C" void brainrot_live_tick(const BrainrotLiveAPI* api,double dt) {
    (void)dt;
    // Example: user can modify gameplay rules safely through API callbacks.
    // Avoid unbounded loops or blocking operations in this callback.
    if(!api || api->abi_version!=BRAINROT_LIVE_ABI)return;
    // Uncomment to place stone when the corresponding chunk is loaded:
    // api->set_block(api->userdata,0,65,0,3);
}
