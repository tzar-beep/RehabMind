import { z } from "zod";

export const RoleSchema = z.enum(["patient", "clinician", "admin"]);
export type Role = z.infer<typeof RoleSchema>;

export const MeSchema = z.object({
  id: z.string(),
  role: RoleSchema,
  display_name: z.string(),
});
export type Me = z.infer<typeof MeSchema>;

export const PatientSchema = z.object({ id: z.string(), display_name: z.string() });
export type Patient = z.infer<typeof PatientSchema>;

export const UserSummarySchema = z.object({
  id: z.string(),
  email: z.string(),
  role: RoleSchema,
  display_name: z.string(),
  is_active: z.boolean(),
});
export type UserSummary = z.infer<typeof UserSummarySchema>;

export const ROLE_HOME: Record<Role, string> = {
  patient: "/patient",
  clinician: "/clinician",
  admin: "/admin",
};
