# Sessions
The plugin server has a small session manager API. It uses MongoDV for the backend. The MongoDB must have a database set up and should be configured for user authentication. These topics are beyond the scope of this document, but you may visit the [MongoDB Documentation](https://www.mongodb.com/docs/) on how to set up and configure the database.

## Sessman API
The sessman API uses the following endpoints: 

|Endpoint          | Usage and Parameters                                       |
|------------------|------------------------------------------------------------|
| /sessman/new     |  userid: user id associated with the session being created |
|                  |  data: should be sent as POST data, in JSON format.        |
| /sessman/update  |  data: should be sent as POST data, in JSON format.        |
| /sessman/get     | sessionid: The session ID given from /sessman/new          |
|                  | userid: The userid used with /sessman/new                  |

The basic flow is to create a sessions with `/sessman/new`, or etrieve an existing session, `/sessman/get`. As data is updted, `/sessman/update` is called to update the session data. 

Session data automatically expires after session_ttl. 

All data from sessman are returned as JSON objects.

## Configuration
Configuring the sessman plugin is a little different from other plugins, and, in fact introduced the JSON config interpolator. In the [config](Config.md) file, under plugin_parms, a line is needed for the JSON config:

```ini
[plugin_parms]
sessman=json=sessman.json
```

And the sessman.json file:

```json
{
  "username": "ps_sessman",
  "password": "<your secure password here>",
  "server_url": "mongo.domain.tld:27017",
  "database": "sessman",
  "session_ttl": 86400,
}
```

The purpose of JSON is it allow for storing passwords that may cause parsing errors with [configparser](https://docs.python.org/3/library/configparser.html). The parameters needed 
are: 

|Parameter      |Usage                                               |
|---------------|----------------------------------------------------|
| username      | Username for the MongoDB database                  |
| password      | Password for the MongoDB database                  |
| server_url    | URL for the MongoDB server                         |
| session_ttl   | Time to live for the session entries, in seconds.  |


## Example Javascript Session Class

```javascript
class Session {
    //
    // Session is a class to implement expiring session data.
    // a session is created, with a session id, which is stored in the class
    // the data is available in Session.data.<key>. When the data is modified
    // and the updateSession method is called, the session is updated and its expiry is
    // reset
    //
    //  Most of the methods are async and need to be called accordingly.
    //  To properly create a session use:
    //      Session.create(user, options)
    //
    // Options are:
    //     options = {
    //          base_url: the base portion of the url for url construction
    //          data: javascript object of initial session data
    //          auth: this is the apikey configured and sent in headers as a bearer token
    //     }
    constructor(user,  user_options) {
        this.options = {
            'base_url':  "http://hp.ducksfeet.com:6123/sessman",
            'auth': null,
            'data': {},
        }
        if (user_options && typeof user_options == 'object')
            Object.assign(this.options, user_options);
        this.base_url = this.options.base_url;
        this.user = user;
        this.data = this.options.data;
        console.log('base_url',this.base_url,'user',this.user,'data', this.data);
    }
     static async create(user, options) {
        const instance = new Session(user, options);
        await instance.createSession();
        return instance;
      }
      get_command_url(command, parameters) {
        // take object parameters and create a query string
        // then create the url for the endppoint
        let qry_str = '';
        if (parameters && typeof parameters === 'object') {
            Object.keys(parameters).forEach(k => {
                if (qry_str)
                    qry_str = `${parms}&${k}=${parameters[k]}`;
                else
                    qry_str = `${k}=${parameters[k]}`;
            });
        }
        return `${this.base_url}/${command}?${qry_str}`;
    }
    async get_data(cmd, parameters, data) {
        let rdata = undefined;
        let method = 'POST';
        let body = "";
        let url = this.get_command_url(cmd, parameters);
        let headers = {'Content-type': 'text/javascript'}
        if (data !== undefined) {
            body = JSON.stringify({
                'data': data
            });
        }
        if (this.options.auth)
            headers['Authorization'] = `Bearer ${self.options.auth}`

        console.log(`get_data: [url=${url}]`)
        console.log(`get_data: [headers=${JSON.stringify(headers)}]`)
        console.log(`get_data: [data=${JSON.stringify(data)}]`)
        const response = await fetch(url, {
            'headers': headers,
            'method': method,
            'body': body
        });

        if (response.ok) {
            try {
                const responseText = await response.text(); // Read the response body as text
                const jsonData = JSON.parse(responseText); // Then parse it as JSON
                return jsonData;
            } catch (e) {
                console.error("Error parsing JSON:", e);
                const textData = await response.text();
                return textData;
            }
        }
        console.error(`Request failed with status: ${response.status}`);
        return null;
    }
    async createSession() {
        const rdata = await this.get_data('new', { 'user': this.user }, this.data); // Pass this.data as the request body
            if (typeof rdata == 'object') {
            console.log('Create session, data:', rdata);
            if (rdata && rdata.session_id && rdata.data) {
                this.session_id = rdata.session_id;
                this.data = rdata.data;
            } else {
                console.error("Error: Invalid data received during session creation: ", rdata);
            }
        }
    }
    async updateSession() {
        const rdata = await this.get_data('update', {
            'session_id': this.session_id
        }, this.data);
        if (rdata && rdata.data) {
            this.data = rdata.data;
        } else {
            console.error("Error: Invalid data received during session update.");
        }
    }
}
```