# Control Resilience Management

> Control Resilience Management
> CRAAX - UPC, 2019

---

- [Description](#Description)
- [Leader Election](#Leader Election)
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
    - Passive Leader Promotion (PLP)
    - Automatic Leader Promotion (ALP)
- On running
    - On failure: Leader Protection (LP)
    - On reelection: Leader Reelection (LR)
    
##### Passive Leader Promotion (PLP)

The agent is manually set to start as a Leader, using the environment variable `isLeader` set to `True`. By default, an agent starts as a normal agent.

##### Automatic Leader Election (ALP)

If the *PLP* result on a non-leader state, the agent starts to scan for nearby leaders in the location. If no leader is found given a period defined by policy, the *ALP* starts the agent as a Leader **IF** the agent is capable. The capability of an agent to be a leader is defined by the Leader Election Algorithm. 

##### Leader Protection (LP)

Once the leader is setup and running, the Area Resilience submodule starts looking for an agent to become the backup. The backup checks if the leader is running correctly using the Keepalive Protocol defined in the module. Either the Leader or the Backup are protected, meaning that if the Leader fails, the backup takes its place or if the backup fails, the leader elects a new one when it's possible. The election is performed using the Leader Election Algorithm.

##### Leader Reelection (LR)

When is necessary to replace the actual Leader, the reelection mechanism allow us to select a new agent to be the Leader and demote the current one into a normal agent.
 

### API Endpoints

All the API calls are made via REST. The endpoints and required parameters can be consulted on [http://{policies_address}:46050/](http://localhost:46050/)

**Note:** Replace *policies_address* with the real address of the container or device where the code is running

**IMPORTANT**: The new route to the policies module is now `api/v2/resource-management/policies`

#### Resource Manager Status

Get resource manager module start status and errors on triggers.

- **GET**  /rm/components

```bash
curl -X GET "http://localhost/rm/components" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Success
    - **Response Payload:** 
    ```json
    {
  "started": true,                              // The agent is started
  "running": true,                              // The agent is currently running
  "modules": [                                  // List of modules that are triggered on starting
    "string"
  ],
  "discovery": true,                            // Discovery module is started
  "identification": true,                       // Identification module is started
  "cau_client": true,                           // CAUClient module is started
  "categorization": true,                       // Categorization module is started
  "policies": true,                             // Area Resilience module is started
  "discovery_description": "string",            // Discovery module description / parameters received
  "identification_description": "string",       // Identification module description / parameters received
  "categorization_description": "string",       // Categorization module description / parameters received
  "policies_description": "string",             // Policies module description / parameters received
  "cau_client_description": "string"            // CAUClient module description / parameters received
    }
    ```

#### Keepalive

Keepalive entrypoint for Leader. Backups send message to this address and check if the Leader is alive. Only registered backups are allowed to send keepalives, others will be rejected.

- **POST** /api/v2/resource-management/policies/keepalive
- **PAYLOAD**  `{"deviceID": "agent/1234"}`

```bash
curl -X POST "http://localhost/api/v2/resource-management/policies/keepalive" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
```

- **RESPONSES**
    - **200** - Success
    - **403** - Agent not authorized
    - **405** - Device is not a Leader
    - **Response Payload:** `{
  "deviceID": "leader/1234",
  "backupPriority": 0
}` 

#### Leader Info

Check if the agent is a Leader or Backup.

- **GET** /api/v2/resource-management/policies/leaderinfo

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/leaderinfo" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Success
    - **Response Payload:** `{
  "imLeader": false,
  "imBackup": false
}`

#### Reelection

Send a message to trigger the reelection process. The specified agent will be the reelected leader if it accepts.

- **POST** /api/v2/resource-management/policies/reelection
- **PAYLOAD** `{
  "deviceID": "agent/1234"
}`

```bash
curl -X POST "http://localhost/api/v2/resource-management/policies/reelection" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
```

- **RESPONSES**
    - **200** - Reelection Successful
    - **401** - The Agent is not authorized to trigger the reelection
    - **403** - Reelection failed
    - **404** - Device not found or IP not available
    - **Response Payload:** `{
  "imLeader": false,
  "imBackup": false
}`

#### Start Area Resilience

Starts the Area Resilience submodule (in charge of the Leader Protection)

- **GET** /api/v2/resource-management/policies/startAreaResilience

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/startAreaResilience" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started
    
#### Start Agent

Start the agent (start as Leader or Normal agent + Discovery, CAU Client and Categorization Triggers)

- **GET** /api/v2/resource-management/policies/policiesstartAgent

```bash
curl -X GET "http://localhost/api/v2/resource-management/policiesstartAgent" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started

    
#### Role Change

Change the agent from current role to specified one (leader, backup or agent).

- **GET** /api/v2/resource-management/policies/roleChange/{role}

```bash
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/agent" -H "accept: application/json"
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/backup" -H "accept: application/json"
curl -X GET "http://localhost/api/v2/resource-management/policies/roleChange/leader" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Successful
    - **403** - Not Successful
    - **404** - Role not found

### LICENSE

The Policies module application is licensed under [Apache License, Version 2.0](LICENSE.txt)
