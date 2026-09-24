"use client";

import Link from "next/link";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {Brand} from "@/components/Brand";
import {api} from "@/lib/api";

type Form={token:string;password:string;confirmPassword:string};

export default function ResetPassword(){
  const {register,handleSubmit,setValue,setError:flagError,formState:{errors,isSubmitting}}=useForm<Form>();
  const [error,setError]=useState("");
  const [complete,setComplete]=useState(false);

  useEffect(()=>{
    const token=new URLSearchParams(window.location.search).get("token");
    if(token)setValue("token",token);
  },[setValue]);

  async function submit(v:Form){
    if(v.password!==v.confirmPassword){
      flagError("confirmPassword",{message:"Passwords must match."});
      return;
    }
    try{
      setError("");
      await api<{status:string;sessions_revoked:boolean}>("/api/v1/auth/password-reset/confirm",{
        method:"POST",
        body:JSON.stringify({token:v.token,password:v.password}),
      });
      setComplete(true);
    }catch{
      setError("This recovery link is invalid or expired. Request a new one.");
    }
  }

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Choose a new password</h1>
      <p>Completing recovery revokes existing sessions for this account.</p>
      {complete?<div className="success" role="status">Password updated. <Link href="/login">Log in with your new password</Link>.</div>:<form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Recovery token<input type="text" autoComplete="one-time-code" required {...register("token")}/></label>
        <label className="field">New password<input type="password" autoComplete="new-password" required minLength={8} {...register("password")}/></label>
        <label className="field">Confirm new password<input type="password" autoComplete="new-password" required minLength={8} {...register("confirmPassword")}/></label>
        {errors.confirmPassword?.message&&<div className="error" role="alert">{errors.confirmPassword.message}</div>}
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Updating…":"Update password"}</button>
      </form>}
      <p className="authNote"><Link href="/forgot-password">Request a new recovery link</Link>.</p>
    </section>
  </main>;
}
