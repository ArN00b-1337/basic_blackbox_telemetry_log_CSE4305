#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    float altitude, airspeed, pitch;
    int time;

    struct Node *next;
    struct Node *prev;

} Node;

int main() {

    Node *head = NULL, *tail = NULL, *newNode, *temp;
    int n, i;

    printf("Enter number of flight records: ");
    scanf("%d", &n);

    for(i = 0; i < n; i++) {

        newNode = (Node*) malloc(sizeof(Node));

        printf("\nRecord %d\n", i + 1);

        printf("Enter Altitude: ");
        scanf("%f", &newNode->altitude);

        printf("Enter Airspeed: ");
        scanf("%f", &newNode->airspeed);

        printf("Enter Pitch Angle: ");
        scanf("%f", &newNode->pitch);

        printf("Enter Timestamp: ");
        scanf("%d", &newNode->time);

        newNode->next = NULL;
        newNode->prev = NULL;

        if(head == NULL) {
            head = tail = newNode;
        }
        else {
            tail->next = newNode;
            newNode->prev = tail;
            tail = newNode;
        }
    }

    printf("\n--- Flight Log (Forward Traversal) ---\n");
    temp = head;
    while(temp != NULL) {
        printf("T+%ds | Altitude: %.1f | Speed: %.1f | Pitch: %.1f\n",
               temp->time,
               temp->altitude,
               temp->airspeed,
               temp->pitch);
        temp = temp->next;
    }

    printf("\n--- Crash Analysis (Backward Traversal) ---\n");
    temp = tail;
    while(temp != NULL) {
        printf("T+%ds | Altitude: %.1f | Speed: %.1f | Pitch: %.1f\n",
               temp->time,
               temp->altitude,
               temp->airspeed,
               temp->pitch);
        temp = temp->prev;
    }

    temp = head;
    while(temp != NULL) {
        Node *del = temp;
        temp = temp->next;
        free(del);
    }

    printf("\nMemory Cleared.\n");
    return 0;
}

