"use client";

import {useQueryClient} from "@tanstack/react-query";
import Link from "next/link";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {authHref,intendedDestination} from "@/lib/auth-destination";
import {useRouter} from "next/navigation";
import {usePublicSession} from "@/components/AuthActions";
import {AuthFrame} from "@/components/AuthFrame";
import {api,setCsrfToken} from "@/lib/api";
import {authErrorMessage} from "@/lib/auth";

type Form={email:string;password:string};

export default function Login(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>();
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [showPassword,setShowPassword]=useState(false);
  const router=useRouter();
  const queryClient=useQueryClient();
  const session=usePublicSession();
  const [destination,setDestination]=useState("/workspace");
  useEffect(()=>setDestination(intendedDestination()),[]);
  useEffect(()=>{if(session.data?.authenticated&&session.data.email_verified)router.replace(intendedDestination())},[session.data,router]);

  useEffect(()=>{
    const query=new URLSearchParams(window.location.search);
    const fragment=new URLSearchParams(window.location.hash.replace(/^#/,""));
    if(query.get("error")||fragment.get("error")||query.get("error_code")||fragment.get("error_code")){
      setError("This email verification link is invalid or expired. Request a new verification link.");
    }else if(query.get("verified")==="1"){
      setNotice("Log in to continue after verifying your email.");
    }
    for(const key of ["access_token","refresh_token","token_hash","token","code","error","error_code","error_description"])query.delete(key);
    const remaining=query.toString();
    if(window.location.hash||remaining!==window.location.search.replace(/^\?/,""))window.history.replaceState(null,"",`${window.location.pathname}${remaining?`?${remaining}`:""}`);
  },[]);

  async function submit(v:Form){
    try{
      setError("");
      const r=await api<{csrf_token:string}>("/api/v1/auth/web/login",{
        method:"POST",
        body:JSON.stringify(v),
      });
      setCsrfToken(r.csrf_token);
      await queryClient.invalidateQueries({queryKey:["public-session"]});
      const destination=intendedDestination();sessionStorage.removeItem("rivexis_pending_destination");
      router.replace(destination);
    }catch(e){
      setError(authErrorMessage(e,"login"));
    }
  }

  return <AuthFrame mode="login">
      <h1>Log in</h1>
      <p>Access your Rivexis workspace.</p>
      {notice&&<div className="success" role="status">{notice}</div>}
      <form className="form" method="post" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        <div className="passwordField"><label className="field">Password<input type={showPassword?"text":"password"} autoComplete="current-password" required minLength={8} {...register("password")}/></label><button className="passwordReveal" type="button" aria-label={showPassword?"Hide password":"Show password"} aria-pressed={showPassword} onClick={()=>setShowPassword(!showPassword)}>{showPassword?"Hide":"Show"}</button></div>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" type="submit" disabled={isSubmitting}>{isSubmitting?"Logging in…":"Log in"}</button>
      </form>
      <p className="authNote"><Link href="/forgot-password">Forgot your password?</Link> <Link href="/verify-email">Verify an existing account</Link>. Need an account? <Link href={authHref("/signup",destination)}>Create one</Link>.</p>
  </AuthFrame>;
}
