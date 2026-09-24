"use client";

import Link from "next/link";
import {useState} from "react";
import {useForm} from "react-hook-form";
import {Brand} from "@/components/Brand";
import {api} from "@/lib/api";

type Form={email:string};

export default function ForgotPassword(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>();
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

  return <main className="formPage">
    <section className="formCard">
      <Brand/>
      <h1>Reset password</h1>
      <p>Request a one-time recovery link. The response is identical whether or not the address is registered.</p>
      {accepted?<div className="success" role="status">If an eligible account exists, a password reset email has been sent.</div>:<form className="form" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" disabled={isSubmitting}>{isSubmitting?"Requesting…":"Send reset link"}</button>
      </form>}
      <p className="authNote"><Link href="/login">Return to login</Link>.</p>
    </section>
  </main>;
}
