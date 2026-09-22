export interface CurrentUser {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    roles: string[];
}
