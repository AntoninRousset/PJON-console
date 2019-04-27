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
#include <stddef.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>

#define SOCKET_FILE "/tmp/PJON.sock"
#define MSG_LENGTH 2048

int open_socket(const char *filename)
{
	int sock = socket(PF_LOCAL, SOCK_STREAM, 0);
	if (sock < 0) {
		perror ("socket");
		exit (EXIT_FAILURE);
	}


	struct sockaddr_un name;
	memset(&name, 0, sizeof(name));
	name.sun_family = AF_LOCAL;
	name.sun_path[0] = '\0';
	socklen_t size = strlen(name.sun_path);
	bind(sock, (struct sockaddr*) &name, size);

	strncpy(name.sun_path+1, filename, strlen(filename));
	size = offsetof(struct sockaddr_un, sun_path) + strlen(filename) + 1;
	if (connect(sock, (struct sockaddr*) &name, size) < 0) {
		perror("connect");
		exit(EXIT_FAILURE);
	}

	return sock;
}

int write_socket(int sock, const char* data, size_t size)
{
	ssize_t count = send(sock, data, size, 0);
	if (count < 0)
		perror("Send");
	return count;
}

// I am too stupid to create a function that take int* master, int* slave and
// returns the name of the file
int open_pty()
{
	int master = posix_openpt(O_RDWR);
	if (master < 0) {
		perror("open");
		exit(EXIT_FAILURE);
	}

	if (grantpt(master) < 0) {
		perror("grant");
		exit(EXIT_FAILURE);
	}

	if (unlockpt(master) < 0) {
		perror("unlock");
		exit(EXIT_FAILURE);
	}
	return master;
}

// Can we write a single function 'write' for all fd?
int write_pty(int fd, const char* msg, size_t size)
{
	ssize_t count = write(fd, msg, size);
	if (count < 0)
		perror("write pty");
	return count;
}

int main()
{
	int sock = open_socket(SOCKET_FILE);

	int master_pty = open_pty();
	char* name_pty = ptsname(master_pty);
	if (name_pty == NULL) {
		perror("name pty");
		close(master_pty);
		exit(EXIT_FAILURE);
	}
	printf("PTY on %s\n", name_pty);

	int slave_pty = open(name_pty, O_WRONLY);
	if (slave_pty < 0) {
		perror("slave pty");
		close(master_pty);
		exit(EXIT_FAILURE);
	}

	char buffer[MSG_LENGTH];
	ssize_t count;

	int pid = fork();
	if (pid < 0) {
		perror("fork");
	}

	if (pid == 0) {
		while (1) {
			count = read(master_pty, &buffer, sizeof(buffer));
			if (count < 0) {
				perror("Read pty");
				return EXIT_FAILURE;
			}
			printf("read from pty: %s\n", buffer);
			write_socket(sock, buffer, strlen(buffer)+1);
		}
	} else {
		while (1) {
			fgets(buffer, MSG_LENGTH, stdin);
			write_pty(slave_pty, buffer, strlen(buffer)+1);
		}
	}

	shutdown(sock, 0);
	shutdown(slave_pty, 0);
	close(master_pty);
	return EXIT_SUCCESS;
}
