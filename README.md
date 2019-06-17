# Control Resilience Management

> Control Resilience Management

> Alejandro Jurnet, 2019

------

### Description

The CRM module is responsible for:

- Define the resilience and clustering policies.
- Enforce the protection of the area (Leader and Backup).
- Definition and Execution of the Leader Election Algorithm.
- Orchestration of the Resource Manager Block.
- Distribution of the active defined Policies.


## Usage

The CRM module can be run using the dockerized version or directly from source.

#### Docker

Build source version: `docker build -f Dockerfile -t CRM .`

Run CRM in Docker: `docker run --rm -p 46050:46050 --env DEBUG=False --env DEVICEID=agent/0 --env isLeader=True --env BROADCASTADDR=192.168.5.255 --name agent0 CRM` 

#### Source

`Python 3.7.x` is required to execute this code.

1. Clone the repository with Git. It's hightly recomended to create a Python virtual environment.
2. Install all the library dependencies: `pip3 install -r requirements.txt`
2. Execute the following command: `python3 main.py`


### Leader Election

The Leader Election process is defined by **four** policies that can be activated at different instants of time. We group them into two groups depending on the state of the agent:

- On startup
    - Passive Leader Promotion (PLP)
    - Automatic Leader Promotion (ALP)
- On running
    - On failure: Area Resilience (AR)
    - On reelection: Leader Reelection (LR)
    
##### Passive Leader Promotion (PLP)

The agent is manually set to start as a Leader, using the environment variable `isLeader` set to `True`. By default, an agent starts as a normal agent.

##### Automatic Leader Election (ALP)

If the *PLP* result on a non-leader state, the agent starts to scan for nearby leaders in the location. If no leader is found given a period defined by policy, the *ALP* starts the agent as a Leader **IF** the agent is capable. The capability of an agent to be a leader is defined by the Leader Election Algorithm. 

##### Area Resilience (AR)

Once the leader is setup and running, the Area Resilience submodule starts looking for an agent to become the backup. The backup checks if the leader is running correctly using the Keepalive Protocol defined in the module. Either the Leader or the Backup are protected, meaning that if the Leader fails, the backup takes its place or if the backup fails, the leader elects a new one when it's possible. The election is performed using the Leader Election Algorithm.

##### Leader Reelection (LR)

When is necessary to replace the actual Leader, the reelection mechanism allow us to select a new agent to be the Leader and demote the current one into a normal agent.
 

### API Endpoints

All the API calls are made via REST. The endpoints and required parameters can be consulted on [http://{CRM_address}:46050/](http://localhost:46050/)

**Note:** Replace *CRM_address* with the real address of the container or device where the code is running



#### Keepalive

Keepalive entrypoint for Leader. Backups send message to this address and check if the Leader is alive. Only registered backups are allowed to send keepalives, others will be rejected.

- **POST** /crm-api/keepalive
- **PAYLOAD**  `{"deviceID": "agent/1234"}`

```bash
curl -X POST "http://localhost:46050/crm-api/keepalive" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
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

- **GET** /crm-api/leaderinfo

```bash
curl -X GET "http://localhost:46050/crm-api/leaderinfo" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Success
    - **Response Payload:** `{
  "imLeader": false,
  "imBackup": false
}`

#### Reelection

Send a message to trigger the reelection process. The specified agent will be the reelected leader if it accepts.

- **POST** /crm-api/reelection
- **PAYLOAD** `{
  "deviceID": "agent/1234"
}`

```bash
curl -X POST "http://localhost:46050/crm-api/reelection" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/1234\"}"
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

- **GET** /crm-api/startAreaResilience

```bash
curl -X GET "http://localhost:46050/crm-api/startAreaResilience" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started
    
#### Start Agent

Start the agent (start as Leader or Normal agent + Discovery, CAU Client and Categorization Triggers)

- **GET** /crm-api/startAgent

```bash
curl -X GET "http://localhost:46050/crm-api/startAgent" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Started
    - **403** - Already Started

    
#### Role Change

Change the agent from current role to specified one (leader, backup or agent).

- **GET** /crm-api/roleChange/{role}

```bash
curl -X GET "http://localhost:46050/crm-api/roleChange/agent" -H "accept: application/json"
curl -X GET "http://localhost:46050/crm-api/roleChange/backup" -H "accept: application/json"
curl -X GET "http://localhost:46050/crm-api/roleChange/leader" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Successful
    - **403** - Not Successful
    - **404** - Role not found
    
    
#### Distribute Policies

Distribute the current policies to the attached devices.

- **GET** /crm-api/PoliciesDistributionTrigger

```bash
curl -X GET "http://localhost:46050/crm-api/PoliciesDistributionTrigger" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Trigger accepted


#### Set new active Policies

Define new active policies for the Agent.

- **POST** /crm-api/receiveNewPolicies

```bash
curl -X POST "http://localhost:46050/crm-api/receiveNewPolicies" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"LPP\": \"{\\\"TIME_KEEPALIVE\\\": 1.5}\"}"
```

- **RESPONSES**
    - **200** - Policies correctly received
    - **400** - Message malformation


#### Get current Policies

Retrieve the active policies on the device.

- **GET** /crm-api/getCurrentPolicies

```bash
curl -X GET "http://localhost:46050/crm-api/getCurrentPolicies" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Policies received
    - **Response Payload:** `{
  "LMR": "{\"RAM_MIN\": 2000.0}",
  "LDR": "{\"DISK_MIN\": 2000.0}",
  "PLSP": "{\"PLP_ENABLED\": true}",
  "ALSP": "{\"MAX_MISSING_SCANS\": 10, \"ALP_ENABLED\": false}",
  "LPP": "{\"BACKUP_MINIMUM\": 1, \"BACKUP_MAXIMUM\": null, \"MAX_TTL\": 30.0, \"MAX_RETRY_ATTEMPTS\": 5, \"TIME_TO_WAIT_BACKUP_SELECTION\": 3, \"TIME_KEEPALIVE\": 1.5, \"TIME_KEEPER\": 0.1}",
  "LRP": "{\"REELECTION_ALLOWED\": true}",
  "DP": "{\"SYNC_ENABLED\": false, \"SYNC_PERIOD\": 60.0}"
}`


#### Light Discovery Module control

Management of the Light Discovery module status and mode.

- **GET** /ld/control/{mode}/{operation}

```bash
curl -X GET "http://localhost:46050/ld/control/beacon/start" -H "accept: application/json"
curl -X GET "http://localhost:46050/ld/control/beacon/stop" -H "accept: application/json"
curl -X GET "http://localhost:46050/ld/control/scan/start" -H "accept: application/json"
curl -X GET "http://localhost:46050/ld/control/scan/stop" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Successful operation
    - **400** - Error on operation
    - **404** - Mode/Operation not found


#### Beacon Reply

Reception of the reply to a received beacon.

- **POST** /ld/beaconReply

```bash
curl -X POST "http://localhost:46050/ld/beaconReply" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"deviceID\": \"agent/007\", \"deviceIP\": \"\", \"cpu_cores\": 7, \"mem_avail\": 7, \"stg_avail\": 7}"
```

- **RESPONSES**
    - **200** - Device added/modified on the topology
    - **400** - Error on beacon reply message
    

#### Get current Topology

Get the current topology of the Area (Leaders only).

- **GET** /ld/topology

```bash
curl -X GET "http://localhost:46050/ld/topology" -H "accept: application/json"
```

- **RESPONSES**
    - **200** - Topology Successful received
    - **Response Payload:** `{
  "topology": [
    [
      "agent/007",
      "192.168.56.1"
    ]
  ]
}`

#### Resource Manager Status

Get Start Agent module start status and errors on triggers.

- **GET**  /rm/components

```bash
curl -X GET "http://localhost:46050/rm/components" -H "accept: application/json"
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

### LICENSE

The CRM module application is licensed under [Apache License, Version 2.0](LICENSE.txt)
