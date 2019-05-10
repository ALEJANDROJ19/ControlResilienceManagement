# Control Resilience Management

> Policies - Resource Management
> CRAAX - UPC, 2019
> The Policies module is a component of the European Project mF2C.

---

- [Description](#Description)
- [Leader Election](#Leader Election)
    - [Passive Leader Election (PLE)](#Passive Leader Election (PLE))
    - [Automatic Leader Election (ALE)](#Automatic Leader Election (ALE))
    - [Leader Protection (LP)](#Leader Protection (LP))
    - [Leader Reelection (LR)](#Leader Reelection (LR))
- [API Endpoints](#API Endpoints)
- [LICENSE](#LICENSE)

----

### Description

The policies module is responsible for:

- Define the resilience and clustering policies.
- Enforce the protection of the area (Leader and Backup).
- Definition and Execution of the Leader Election Algorithm.
- Orchestration of the Resource Manager Block.

### Leader Election

The Leader Election process is defined by **four** policies that can be activated at different instants of time. We group them into two groups depending on the state of the agent:

- On startup
    - Passive Leader Election (PLE)
    - Automatic Leader Election (ALE)
- On running
    - On failure: Leader Protection (LP)
    - On reelection: Leader Reelection (LR)
    
##### Passive Leader Election (PLE)

The agent is manually set to start as a Leader, using the environment variable `isLeader` set to `True`. By default, an agent starts as a normal agent.

##### Automatic Leader Election (ALE)

If the *PLE* result on a non-leader state, the agent starts to scan for nearby leaders in the location. If no leader is found given a period defined by policy, the *ALE* starts the agent as a Leader **IF** the agent is capable. The capability of an agent to be a leader is defined by the Leader Election Algorithm. 

##### Leader Protection (LP)

Once the leader is setup and running, the Area Resilience submodule starts looking for an agent to become the backup. The backup checks if the leader is running correctly using the Keepalive Protocol defined in the module. Either the Leader or the Backup are protected, meaning that if the Leader fails, the backup takes its place or if the backup fails, the leader elects a new one when it's possible. The election is performed using the Leader Election Algorithm.

##### Leader Reelection (LR)

When is necessary to replace the actual Leader, the reelection mechanism allow us to select a new agent to be the Leader and demote the current one into a normal agent.
 

### API Endpoints

All the API calls are made via REST. The endpoints and required parameters can be consulted on [http://{policies_address}:46050/](http://localhost:46050/)

**Note:** Replace *policies_address* with the real address of the container or device where the code is running

**IMPORTANT**: The new route to the policies module is now `api/v2/resource-management/policies`

// TODO: Add endpoints and CURL example calls

### LICENSE

The Policies module application is licensed under [Apache License, Version 2.0](LICENSE.txt)
