import {ApiError} from "./api";

export type AuthSurface="login"|"signup"|"onboarding";

export function authErrorMessage(error:unknown,surface:AuthSurface):string{
  const status=error instanceof ApiError?error.status:null;

  if(surface==="login"){
    if(status===401)return "Invalid email or password.";
    if(status===403)return "Email verification is required before login.";
    if(status===429)return "Too many login attempts. Try again shortly.";
    if(status===503)return "Authentication service is temporarily unavailable.";
    return "Unable to log in. Try again.";
  }

  if(surface==="signup"){
    if(status===409)return "Unable to create account with those details.";
    if(status===422)return "Check your email, password, and role, then try again.";
    if(status===429)return "Too many signup attempts. Try again shortly.";
    if(status===503)return "Account creation is temporarily unavailable.";
    return "Unable to create account. Try again.";
  }

  if(status===401)return "Your session ended. Log in again to continue onboarding.";
  if(status===403)return "Your session cannot complete this workspace setup.";
  if(status===503)return "Workspace setup is temporarily unavailable.";
  return "Workspace setup could not be completed. Your progress is safe to retry.";
}
