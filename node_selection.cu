#include <curand_kernel.h>

extern "C"
{
#define AUXILIARY_NODE_ID -1

    typedef struct node
    {
        int id;
        node *prev;
        node *next;
        __device__ node(int id) : id(id){};
    } node_t;

    __global__ void init_rng(int nthreads, curandState *states, unsigned long long seed, unsigned long long offset)
    {
        int id = blockIdx.x * blockDim.x + threadIdx.x;
        if (id >= nthreads)
            return;
        /* Each thread gets same seed, a different sequence number, no offset */
        curand_init(seed, id, offset, &states[id]);
    }

    __global__ void generate_rr_sets(float *data, int *rows, int *cols, bool *out, int numNodes, int numNonZeros, int numSets, curandState *states)
    {
        const unsigned int tid = blockDim.x * blockIdx.x + threadIdx.x;
        if (tid < numSets)
        {
            curandState state = states[tid];

            /* Because C does not give us the luxury of dynamic arrays, to imitate the
        behavior of a stack, I am using a linked list*/
            int randomNodeId = ceil(numNodes * curand_uniform(&state)) - 1;
            node *stack = new node(randomNodeId);
            node *auxiliary = new node(AUXILIARY_NODE_ID);
            auxiliary->next = stack;
            stack->prev = auxiliary;

            // Returns false when stack is NULL
            while (stack->id != AUXILIARY_NODE_ID)
            {
                // pop from stack
                int currentNodeId = stack->id;
                node *temp = stack;
                stack = stack->prev;
                free(temp);

                // If current is not in visited
                if (!out[tid * numNodes + currentNodeId])
                {
                    out[tid * numNodes + currentNodeId] = true;

                    int dataStart = rows[currentNodeId];
                    int dataEnd = rows[currentNodeId + 1];

                    for (unsigned int i = dataStart; i < dataEnd; i++)
                    {
                        if (curand_uniform(&state) < data[i])
                        {
                            // append to stack
                            stack->next = new node(cols[i]);
                            stack->next->prev = stack;
                            stack = stack->next;
                        }
                    }
                }
            }
            free(auxiliary);
        }
    }
}