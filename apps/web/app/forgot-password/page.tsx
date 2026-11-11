"use client";

import {useState} from "react";
import {useForm} from "react-hook-form";
import {AuthFrame} from "@/components/AuthFrame";
import {api} from "@/lib/api";

type Form={email:string};

export default function ForgotPassword(){
  const {register,handleSubmit,formState:{isSubmitting,isReady}}=useForm<Form>();
  const [error,setError]=useState("");
  const [accepted,setAccepted]=useState(false);

  async function submit(v:Form){
    try{
      setError("");
      await api<{status:string}>("/api/v1/auth/password-reset/request",{
        method:"POST",
        body:JSON.stringify(v),
      });
      setAccepted(true);
    }catch{
      setError("Password recovery is temporarily unavailable. Try again shortly.");
    }
  }

  return <AuthFrame mode="recovery">
      <h1>Reset password</h1>
      <p>Request a one-time recovery link. The response is identical whether or not the address is registered.</p>
      {accepted?<div className="success" role="status">Recovery request received. If an eligible account exists, check your inbox for a reset link. Delivery may take a few minutes; check your spam folder too.</div>:<form className="form" method="post" aria-busy={!isReady||isSubmitting} onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")} disabled={!isReady}/></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" type="submit" disabled={!isReady||isSubmitting}>{isSubmitting?"Requesting…":"Send reset link"}</button>
      </form>}
      <p className="authNote"><a href="/login">Return to login</a>.</p>
  </AuthFrame>;
}
