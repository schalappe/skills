# Schema Composition

Reusable patterns for the `components/schemas` block: common shapes, polymorphism, file upload bodies.

## Common schema shapes

```yaml
# String with validation
name:
  type: string
  minLength: 1
  maxLength: 100

# Closed enum
status:
  type: string
  enum: [active, inactive, pending]

# Reference to another schema
user:
  $ref: "#/components/schemas/User"

# Array of refs
items:
  type: array
  items:
    $ref: "#/components/schemas/Item"

# Nullable — OpenAPI 3.1 uses JSON Schema syntax
avatar:
  type: ["string", "null"]
```

## Standard response set

Reusing a `responses` block keeps every endpoint consistent:

```yaml
responses:
  "200":
    description: Success
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/User"
  "400":
    $ref: "#/components/responses/BadRequest"
  "401":
    $ref: "#/components/responses/Unauthorized"
  "404":
    $ref: "#/components/responses/NotFound"
```

## Polymorphism with `oneOf` + discriminator

Use when one endpoint returns or accepts several distinct shapes that share a base. The discriminator tells code generators how to pick the right type.

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
      required: [id, type, createdAt]
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
          required: [to, subject]
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
          required: [phoneNumber, message]
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
          required: [deviceToken, title]
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

### When to choose which composition keyword

| Keyword   | Meaning                              | Use for                                |
| --------- | ------------------------------------ | -------------------------------------- |
| `allOf`   | Combine — must match all schemas     | Inheritance / mixing in a base type    |
| `oneOf`   | Exclusive — must match exactly one   | Tagged-union responses (with discriminator) |
| `anyOf`   | Inclusive — must match one or more   | Validation rules that overlap          |

## File upload

### Single file

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
              required: [file]
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

### Multiple files

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

## Rules

- **Always `$ref` repeated shapes** — duplicating a schema in two endpoints guarantees they drift.
- **Discriminator field must also appear in the variant's `properties`** as a `const`, or generators emit broken types.
- **`format: binary` only inside `multipart/form-data`** — not in JSON bodies.
