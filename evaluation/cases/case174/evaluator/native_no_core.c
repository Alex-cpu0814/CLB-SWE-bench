/* Runtime-only process resource guard for the WSL piped core handler.
 * No interposed functions, signal handlers, allocations or test operations. */
#include <sys/prctl.h>
#include <sys/resource.h>
#include <unistd.h>

__attribute__((constructor)) static void disable_core_dump(void) {
    struct rlimit limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &limit) != 0 ||
        prctl(PR_SET_DUMPABLE, 0UL, 0UL, 0UL, 0UL) != 0) {
        _exit(125);
    }
}
