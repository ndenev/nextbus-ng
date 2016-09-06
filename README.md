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

*   `/api/v1/` - List of API endpoints.
*   `/api/v1/agency` - List of Nexbus agencies. This API implements calls only to "sf-muni".
*   `/api/v1/routes` - List of "sf-muni" routes.
*   `/api/v1/routes/config` - Configuration for all "sf-muni" routes. This call can return a lot of data!.
*   `/api/v1/routes/config/<route_tag>` - Configuration for a given route. Route tags are retrieved using the `/api/v1/routes` endpoint.
*   `/api/v1/notinservice?time=<unix_timestamp>` - List of routes not running at the given time specified by the *unix_timestamp* argument. This call retrieves large amount of data on the backend and can take some time if the redis cache is cold.
*   `/api/v1/notinservice/<route_tag>?time=<unix_timestamp>` - Check if a given route specified by the *route_tag* argument runs at the given time specified by *unix_timestamp*
*   `/api/v1/routes/schedule` - List of all routes schedules if the agency supports it. **NOTE: "sf-muni" does not support this call**
*   `/api/v1/routes/schedule/<route_tag>` - Get the schedules for a given route specified by *<route_tag*.
*   `/api/v1/stats` - Get request statistics for all API endpoints.
*   `/api/v1/stats/slowlog` - Get list of the top 50 slow requests (requests that took more than 2 seconds).

At present the *messages*, *predictions* and *predictionsForMultiStops* API calls are not implemented.

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
