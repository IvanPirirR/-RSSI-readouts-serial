
/* auto-generated by gen_syscalls.py, don't edit */
#ifndef Z_INCLUDE_SYSCALLS_SOCKET_SELECT_H
#define Z_INCLUDE_SYSCALLS_SOCKET_SELECT_H


#ifndef _ASMLANGUAGE

#include <syscall_list.h>
#include <syscall.h>

#include <linker/sections.h>

#if __GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 6)
#pragma GCC diagnostic push
#endif

#ifdef __GNUC__
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
#if !defined(__XCC__)
#pragma GCC diagnostic ignored "-Warray-bounds"
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

extern int z_impl_zsock_select(int nfds, zsock_fd_set * readfds, zsock_fd_set * writefds, zsock_fd_set * exceptfds, struct zsock_timeval * timeout);

__pinned_func
static inline int zsock_select(int nfds, zsock_fd_set * readfds, zsock_fd_set * writefds, zsock_fd_set * exceptfds, struct zsock_timeval * timeout)
{
#ifdef CONFIG_USERSPACE
	if (z_syscall_trap()) {
		/* coverity[OVERRUN] */
		return (int) arch_syscall_invoke5(*(uintptr_t *)&nfds, *(uintptr_t *)&readfds, *(uintptr_t *)&writefds, *(uintptr_t *)&exceptfds, *(uintptr_t *)&timeout, K_SYSCALL_ZSOCK_SELECT);
	}
#endif
	compiler_barrier();
	return z_impl_zsock_select(nfds, readfds, writefds, exceptfds, timeout);
}


#ifdef __cplusplus
}
#endif

#if __GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 6)
#pragma GCC diagnostic pop
#endif

#endif
#endif /* include guard */
