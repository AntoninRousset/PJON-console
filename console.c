/* 
 * This program is free software: you can redistribute it and/or modify  
 * it under the terms of the GNU General Public License as published by  
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License 
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

#define _XOPEN_SOURCE 600 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

#include <pty.h>
#include <termios.h>
#include <fcntl.h>

#include <sys/select.h>
#include <sys/wait.h>

int open_pty()
{
	int master = posix_openpt(O_RDWR);
	if (master < 0) {
		perror("open");
		exit(EXIT_FAILURE);
	}

	return master;
}

int main()
{
	int master = open_pty();
	printf("master number: %d\n", master);

	fd_set set;
	FD_ZERO(&set);
	FD_SET(master, &set);

	char buffer[2048];

	for (;;) {
		if (select(FD_SETSIZE, &set, NULL, NULL, NULL) < 0) {
			perror("select");
			exit(EXIT_FAILURE);
		}

		if (FD_ISSET(master, &set)) {
			read(master, buffer, sizeof(buffer));
			printf("%s", buffer);
		}
	}
	return EXIT_SUCCESS;
}

// We should mutli-thread it, one thread for in, one for out...
