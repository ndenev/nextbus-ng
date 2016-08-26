# NextBus-NG Api

Document version 0.0.1

## Introduction

This project wraps and extends the XML API exposed at webservice.nextbus.com,
and exposes it as scalable JSON REST API.
The following document will lay out some assumptions and design decisions
about this implementation.


## Service Architecture

### Frontend

The client facing frontend is implemented using
the excellent, high-performance non-blocking Webserver/Balancer Nginx.
At the moment redundancy is achieved simply by running two Nginx instances in separate containers using different IPs, which are
used with RR DNS.

#### Frontend Endpoints

*   `/nextbus-ng/v1/cmd<nextbus_api_cmd>?<p1>=<v1>..&<p2=v2>`
*   `/nextbus-ng/v1/notrunning`
*   `/nextbus-ng/v1/stats/hits`
*   `/nextbus-ng/v1/stats/slow`

### Backend

The backend consists of Application servers running the Python Flask framework.
There are two Applications running,
the Api Gateway, and the Api-Ng Application.

#### Backend - Api Gateway

The Api Gateway is serving as a caching NextBus Api gateway, exposing the XML Api as a REST JSON based interface and also providing
configurable caching and rate-limiting to
protect the upstream service.

#### Backend - Api-Ng Application

Flask-Restful[^1] Application

### Caching and Storage

Single (or multiple) Redis instances provide
storage to serve as caching layer for the calls made to [webservice.nextbus.com](webservice.nextbus.com),
 and also as aggregation point of the per

### Technologies

*   docker
*   docker-compose
*   Python
*   Flask
*   Flask-Cache
*   Flask-Restful[^1]
*   redis
*   nginx

## NOTES

The [nextbus.com](nextbus.com) uses the
 concept of *agency* to expose information
 about multiple municipalities and cities.
NextBus-Ng does not support multi-agency setup,
and the agency to be used is configured in the
 App before startup, with the default being
 *sf-muni*.
