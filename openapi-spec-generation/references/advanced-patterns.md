# Advanced OpenAPI Patterns

Advanced patterns for pagination, webhooks, polymorphism, and more.

## Pagination Patterns

### Offset-Based Pagination

```yaml
paths:
  /users:
    get:
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/User"
                  pagination:
                    type: object
                    properties:
                      page:
                        type: integer
                      limit:
                        type: integer
                      total:
                        type: integer
                      totalPages:
                        type: integer
                      hasNext:
                        type: boolean
                      hasPrev:
                        type: boolean
```

### Cursor-Based Pagination

```yaml
paths:
  /events:
    get:
      parameters:
        - name: cursor
          in: query
          description: Cursor from previous response
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/Event"
                  pagination:
                    type: object
                    properties:
                      nextCursor:
                        type: ["string", "null"]
                      hasMore:
                        type: boolean
```

## Webhooks

### Webhook Definition (OpenAPI 3.1)

```yaml
webhooks:
  userCreated:
    post:
      summary: User created event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreatedEvent"
      responses:
        "200":
          description: Webhook processed successfully

  userUpdated:
    post:
      summary: User updated event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserUpdatedEvent"
      responses:
        "200":
          description: Webhook processed successfully

components:
  schemas:
    WebhookEvent:
      type: object
      required:
        - id
        - type
        - timestamp
        - data
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
        timestamp:
          type: string
          format: date-time
        data:
          type: object

    UserCreatedEvent:
      allOf:
        - $ref: "#/components/schemas/WebhookEvent"
        - type: object
          properties:
            type:
              const: user.created
            data:
              $ref: "#/components/schemas/User"

    UserUpdatedEvent:
      allOf:
        - $ref: "#/components/schemas/WebhookEvent"
        - type: object
          properties:
            type:
              const: user.updated
            data:
              type: object
              properties:
                user:
                  $ref: "#/components/schemas/User"
                changes:
                  type: array
                  items:
                    type: string
```

### Webhook Signature Verification Header

```yaml
components:
  headers:
    X-Webhook-Signature:
      description: HMAC-SHA256 signature of the request body
      schema:
        type: string
      example: "sha256=abc123..."
```

## Polymorphism

### Using `oneOf` with Discriminator

```yaml
components:
  schemas:
    Notification:
      oneOf:
        - $ref: "#/components/schemas/EmailNotification"
        - $ref: "#/components/schemas/SMSNotification"
        - $ref: "#/components/schemas/PushNotification"
      discriminator:
        propertyName: type
        mapping:
          email: "#/components/schemas/EmailNotification"
          sms: "#/components/schemas/SMSNotification"
          push: "#/components/schemas/PushNotification"

    NotificationBase:
      type: object
      required:
        - id
        - type
        - createdAt
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
        createdAt:
          type: string
          format: date-time

    EmailNotification:
      allOf:
        - $ref: "#/components/schemas/NotificationBase"
        - type: object
          required:
            - to
            - subject
          properties:
            type:
              const: email
            to:
              type: string
              format: email
            subject:
              type: string
            htmlBody:
              type: string
            textBody:
              type: string

    SMSNotification:
      allOf:
        - $ref: "#/components/schemas/NotificationBase"
        - type: object
          required:
            - phoneNumber
            - message
          properties:
            type:
              const: sms
            phoneNumber:
              type: string
            message:
              type: string
              maxLength: 160

    PushNotification:
      allOf:
        - $ref: "#/components/schemas/NotificationBase"
        - type: object
          required:
            - deviceToken
            - title
          properties:
            type:
              const: push
            deviceToken:
              type: string
            title:
              type: string
            body:
              type: string
            data:
              type: object
              additionalProperties: true
```

## File Upload

### Single File Upload

```yaml
paths:
  /users/{userId}/avatar:
    put:
      operationId: uploadAvatar
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: Image file (max 5MB, jpg/png only)
            encoding:
              file:
                contentType: image/jpeg, image/png
      responses:
        "200":
          description: Avatar uploaded successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  url:
                    type: string
                    format: uri
```

### Multiple File Upload

```yaml
paths:
  /documents:
    post:
      operationId: uploadDocuments
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                files:
                  type: array
                  items:
                    type: string
                    format: binary
                  minItems: 1
                  maxItems: 10
                metadata:
                  type: object
                  properties:
                    category:
                      type: string
                    tags:
                      type: array
                      items:
                        type: string
      responses:
        "201":
          description: Documents uploaded
```

## Batch Operations

### Batch Create

```yaml
paths:
  /users/batch:
    post:
      operationId: batchCreateUsers
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - users
              properties:
                users:
                  type: array
                  items:
                    $ref: "#/components/schemas/CreateUserRequest"
                  minItems: 1
                  maxItems: 100
      responses:
        "200":
          description: Batch results
          content:
            application/json:
              schema:
                type: object
                properties:
                  successful:
                    type: array
                    items:
                      $ref: "#/components/schemas/User"
                  failed:
                    type: array
                    items:
                      type: object
                      properties:
                        index:
                          type: integer
                        error:
                          $ref: "#/components/schemas/Error"
```

## Long-Running Operations

### Async Operation Pattern

```yaml
paths:
  /reports:
    post:
      operationId: generateReport
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ReportRequest"
      responses:
        "202":
          description: Report generation started
          headers:
            Location:
              description: URL to check operation status
              schema:
                type: string
                format: uri
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AsyncOperation"

  /operations/{operationId}:
    get:
      operationId: getOperationStatus
      parameters:
        - name: operationId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Operation status
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AsyncOperation"

components:
  schemas:
    AsyncOperation:
      type: object
      required:
        - id
        - status
        - createdAt
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [pending, processing, completed, failed]
        progress:
          type: integer
          minimum: 0
          maximum: 100
        result:
          oneOf:
            - type: object
            - type: "null"
        error:
          oneOf:
            - $ref: "#/components/schemas/Error"
            - type: "null"
        createdAt:
          type: string
          format: date-time
        completedAt:
          type: ["string", "null"]
          format: date-time
```

## Versioning Strategies

### URL Path Versioning

```yaml
servers:
  - url: https://api.example.com/v1
    description: Version 1
  - url: https://api.example.com/v2
    description: Version 2

paths:
  /users:
    # v1 and v2 have different schemas
```

### Header Versioning

```yaml
paths:
  /users:
    get:
      parameters:
        - name: X-API-Version
          in: header
          required: false
          schema:
            type: string
            enum: ["2024-01-01", "2024-06-01"]
            default: "2024-01-01"
```

## Security Patterns

### Multiple Auth Methods

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key

    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read:users: Read user data
            write:users: Create and update users
            delete:users: Delete users

# Require either JWT OR API key
security:
  - bearerAuth: []
  - apiKey: []

# Specific endpoint requiring OAuth with scopes
paths:
  /admin/users:
    delete:
      security:
        - oauth2: [delete:users]
```
