"use client";

import Link from "next/link";
import {useEffect,useRef,useState} from "react";
import {useForm} from "react-hook-form";
import {AuthFrame} from "@/components/AuthFrame";
import {api} from "@/lib/api";

type Form={token:string;email:string;password:string;confirmPassword:string};

export default function ResetPassword(){
  const {register,handleSubmit,setValue,setError:flagError,formState:{errors,isSubmitting}}=useForm<Form>();
  const [error,setError]=useState("");
  const [complete,setComplete]=useState(false);
  const [hasRecoverySession,setHasRecoverySession]=useState(false);
  const recoverySession=useRef<{access_token:string;refresh_token:string}|null>(null);
  const recoveryHash=useRef<string|null>(null);

  useEffect(()=>{
    const query=new URLSearchParams(window.location.search);
    const fragment=new URLSearchParams(window.location.hash.replace(/^#/,""));
    const tokenHash=query.get("token_hash");
    const token=query.get("token");
    if(token)setValue("token",token);
    const email=query.get("email");
    if(email)setValue("email",email);
    const accessToken=fragment.get("access_token");
    const refreshToken=fragment.get("refresh_token");
    if(accessToken&&refreshToken){
      recoverySession.current={access_token:accessToken,refresh_token:refreshToken};
      setHasRecoverySession(true);
    }else if(tokenHash){
      recoveryHash.current=tokenHash;
      setHasRecoverySession(true);
    }
    for(const key of ["token_hash","token","email"])query.delete(key);
    const remainingQuery=query.toString();
    window.history.replaceState(null,"",`${window.location.pathname}${remainingQuery?`?${remainingQuery}`:""}`);
  },[setValue]);

  async function submit(v:Form){
    if(v.password!==v.confirmPassword){
      flagError("confirmPassword",{message:"Passwords must match."});
      return;
    }
    try{
      setError("");
      const session=recoverySession.current;
      await api<{status:string;sessions_revoked:boolean}>("/api/v1/auth/password-reset/confirm",{
        method:"POST",
        body:JSON.stringify({token:session||recoveryHash.current?undefined:v.token,email:session||recoveryHash.current?undefined:v.email,token_hash:recoveryHash.current??undefined,password:v.password,access_token:session?.access_token,refresh_token:session?.refresh_token}),
      });
      recoverySession.current=null;
      recoveryHash.current=null;
      setComplete(true);
    }catch{
      setError("This recovery link is invalid or expired. Request a new one.");
    }
  }

  return <AuthFrame mode="recovery">
      <h1>Choose a new password</h1>
      <p>Completing recovery revokes existing sessions for this account.</p>
      {complete?<div className="success" role="status">Password updated. <Link href="/login">Log in with your new password</Link>.</div>:<form className="form" method="post" onSubmit={handleSubmit(submit)}>
        {!hasRecoverySession&&<label className="field">Recovery token<input type="text" autoComplete="one-time-code" required {...register("token")}/></label>}
        {!hasRecoverySession&&<label className="field">Email<input type="email" autoComplete="email" {...register("email")}/></label>}
        <label className="field">New password<input type="password" autoComplete="new-password" required minLength={8} {...register("password")}/></label>
        <label className="field">Confirm new password<input type="password" autoComplete="new-password" required minLength={8} {...register("confirmPassword")}/></label>
        {errors.confirmPassword?.message&&<div className="error" role="alert">{errors.confirmPassword.message}</div>}
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" type="submit" disabled={isSubmitting}>{isSubmitting?"Updating…":"Update password"}</button>
      </form>}
      <p className="authNote"><Link href="/forgot-password">Request a new recovery link</Link>.</p>
  </AuthFrame>;
}
