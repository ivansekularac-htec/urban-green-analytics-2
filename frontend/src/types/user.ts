// Must match the `roles.name` values the API seeds.
export const ADMIN_ROLE = 'Admin';

export interface CurrentUser {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    roles: string[];
}

export type User = CurrentUser;

export interface Role {
    id: number;
    name: string;
}

export interface UserRole {
    id: number;
    user_id: number;
    role_id: number;
    farm_id: number | null;
}
