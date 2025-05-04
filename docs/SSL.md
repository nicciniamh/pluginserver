# SSL Configuration

SSL support is optional, but provides a great deal of security when enabled.

SSL is configured in the [configuration](Config.md) file using a similar section as below, which enables SSL and sets up the key and certificate to use. 

```ini
[main]
domain=example.com
[SSL]
enabled=bool:true
keyfile=${ENV:HOME}/etc/certs/${main:domain}-key.pem
certfile=${ENV:HOME}/etc/certs/${main:domain}.pem
```

This sets up the the keys in the user's etc/certs directory for the domain configured in main.


### Why use a properly signed certificate?

A properly signed certificate implies a layer of trust. They can cost as little as nothing, and, when properly configured, may be used for each server on your network - provided they all use the same domain name. 

To set up a free SSL key  you can use, from [EFF](https://eff.org), the [Let's Encrypt](https://letsencrypt.org) service. 

### Why not use self-signed cerficates?

Some of the reasons not to use a signed certificate

* You do not have a domain name or control over a domain name, and its servers
* Your API server runs on an internal network.

### Pitfalls With self-signed certificates. 

* Many Libraries and applications that make use of SSL require a lot of hoops to jump through when using self-signed certificates. 

* Lack of Third-Party Validation: The core issue is that a self-signed certificate isn't verified by a trusted Certificate Authority (CA). When your browser or application encounters a certificate signed by a recognized CA, it has a built-in list of these trusted entities. The CA acts as a neutral third party that has verified the identity of the website or server. With a self-signed certificate, there's no such independent verification. You're essentially saying, "Trust me, I am who I say I am," without any external proof.

* No Identity Assurance: Because there's no validation process, a self-signed certificate offers no real assurance about the identity of the website or server owner. A malicious actor could easily generate a self-signed certificate claiming to be anyone. This makes it impossible for users to confidently verify who they are communicating with.

* Vulnerability to Man-in-the-Middle (MITM) Attacks: Without the validation of a CA, it becomes easier for attackers to intercept communication. An attacker could create their own self-signed certificate, present it to a user, and intercept the encrypted traffic. The user's browser would likely warn them about the untrusted certificate, but if a user ignores this warning (which unfortunately happens), their communication is no longer secure.

* Lack of Revocation Mechanisms: If a CA-signed certificate is compromised, the CA can revoke it, and browsers will be updated with this information, preventing further trust. Self-signed certificates lack this crucial revocation mechanism. If the private key associated with a self-signed certificate is compromised, there's no easy way to inform users or prevent its continued use for malicious purposes.

In essence, self-signed certificates bypass the established system of trust that underpins secure communication on the internet. While they might be acceptable for internal testing or very specific, isolated scenarios where trust is established through other means, they are generally not suitable for public-facing websites or applications where security and user trust are paramount.
