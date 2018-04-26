#include <stdio.h>
#include <unistd.h>

int main(int argc, char ** argv)
{
    int i;

    while (1)
    {
        printf("%d;%d\r\n", i, 10 - i);
        fflush(stdout);

        if (++i > 10)
        {
            i = 0;
        }
        
        usleep(50000);
    }
}