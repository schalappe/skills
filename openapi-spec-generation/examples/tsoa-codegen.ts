// tsoa generates OpenAPI from TypeScript decorators
// This example demonstrates code-first OpenAPI spec generation with Express

import {
  Controller,
  Get,
  Post,
  Patch,
  Delete,
  Route,
  Path,
  Query,
  Body,
  Response,
  SuccessResponse,
  Tags,
  Security,
  Example,
} from "tsoa";

// Models
interface User {
  /** Unique identifier */
  id: string;
  /** User email address */
  email: string;
  /** Display name */
  name: string;
  status: UserStatus;
  role: UserRole;
  /** Avatar URL */
  avatar?: string;
  /** Custom metadata */
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt?: Date;
}

enum UserStatus {
  Active = "active",
  Inactive = "inactive",
  Suspended = "suspended",
  Pending = "pending",
}

enum UserRole {
  User = "user",
  Moderator = "moderator",
  Admin = "admin",
}

interface CreateUserRequest {
  email: string;
  name: string;
  role?: UserRole;
  metadata?: Record<string, unknown>;
}

interface UpdateUserRequest {
  name?: string;
  status?: UserStatus;
  role?: UserRole;
  metadata?: Record<string, unknown>;
}

interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

interface UserListResponse {
  data: User[];
  pagination: Pagination;
}

interface ErrorResponse {
  code: string;
  message: string;
  details?: { field: string; message: string }[];
  requestId?: string;
}

@Route("users")
@Tags("Users")
export class UsersController extends Controller {
  /**
   * List all users with pagination and filtering
   * @param page Page number (1-based)
   * @param limit Items per page (max 100)
   * @param status Filter by user status
   * @param search Search by name or email
   */
  @Get()
  @Security("bearerAuth")
  @Response<ErrorResponse>(400, "Invalid request")
  @Response<ErrorResponse>(401, "Unauthorized")
  @Example<UserListResponse>({
    data: [
      {
        id: "550e8400-e29b-41d4-a716-446655440000",
        email: "john@example.com",
        name: "John Doe",
        status: UserStatus.Active,
        role: UserRole.User,
        createdAt: new Date("2024-01-15T10:30:00Z"),
      },
    ],
    pagination: {
      page: 1,
      limit: 20,
      total: 1,
      totalPages: 1,
      hasNext: false,
      hasPrev: false,
    },
  })
  public async listUsers(
    @Query() page: number = 1,
    @Query() limit: number = 20,
    @Query() status?: UserStatus,
    @Query() search?: string,
  ): Promise<UserListResponse> {
    // Implementation
    throw new Error("Not implemented");
  }

  /**
   * Create a new user
   */
  @Post()
  @Security("bearerAuth")
  @SuccessResponse(201, "Created")
  @Response<ErrorResponse>(400, "Invalid request")
  @Response<ErrorResponse>(409, "Email already exists")
  public async createUser(@Body() body: CreateUserRequest): Promise<User> {
    this.setStatus(201);
    throw new Error("Not implemented");
  }

  /**
   * Get user by ID
   * @param userId User ID
   */
  @Get("{userId}")
  @Security("bearerAuth")
  @Response<ErrorResponse>(404, "User not found")
  public async getUser(@Path() userId: string): Promise<User> {
    throw new Error("Not implemented");
  }

  /**
   * Update user attributes
   * @param userId User ID
   */
  @Patch("{userId}")
  @Security("bearerAuth")
  @Response<ErrorResponse>(400, "Invalid request")
  @Response<ErrorResponse>(404, "User not found")
  public async updateUser(
    @Path() userId: string,
    @Body() body: UpdateUserRequest,
  ): Promise<User> {
    throw new Error("Not implemented");
  }

  /**
   * Delete user
   * @param userId User ID
   */
  @Delete("{userId}")
  @Tags("Users", "Admin")
  @Security("bearerAuth")
  @SuccessResponse(204, "Deleted")
  @Response<ErrorResponse>(404, "User not found")
  public async deleteUser(@Path() userId: string): Promise<void> {
    this.setStatus(204);
  }
}
