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

type Form={email:string;password:string;role:string};
type SignupResponse={csrf_token?:string;verification_required?:boolean;email_status?:string};

export default function Signup(){
  const {register,handleSubmit,formState:{isSubmitting}}=useForm<Form>({defaultValues:{role:"Individual"}});
  const [error,setError]=useState("");
  const [showPassword,setShowPassword]=useState(false);
  const router=useRouter();
  const queryClient=useQueryClient();
  const session=usePublicSession();
  const [destination,setDestination]=useState("/workspace");
  useEffect(()=>setDestination(intendedDestination()),[]);
  useEffect(()=>{if(session.data?.authenticated&&session.data.email_verified)router.replace(intendedDestination())},[session.data,router]);

  async function submit(v:Form){
    try{
      setError("");
      const r=await api<SignupResponse>("/api/v1/auth/web/signup",{
        method:"POST",
        body:JSON.stringify(v),
      });
      const destination=intendedDestination();sessionStorage.setItem("rivexis_pending_destination",destination);
      if(r.verification_required){
        sessionStorage.setItem("rivexis_pending_verification_email",v.email);
        router.replace(authHref("/verify-email",destination,{sent:r.email_status==="accepted"?"1":"0"}));
        return;
      }
      if(!r.csrf_token)throw new Error("Missing authenticated signup session");
      setCsrfToken(r.csrf_token);
      await queryClient.invalidateQueries({queryKey:["public-session"]});
      router.replace(authHref("/onboarding",destination));
    }catch(e){
      setError(authErrorMessage(e,"signup"));
    }
  }

  return <AuthFrame mode="signup">
      <h1>Create an account</h1>
      <p>Save your risk comparisons and retain your decision evidence.</p>
      <form className="form" method="post" onSubmit={handleSubmit(submit)}>
        <label className="field">Email<input type="email" autoComplete="email" required {...register("email")}/></label>
        <div className="passwordField"><label className="field">Password<input type={showPassword?"text":"password"} autoComplete="new-password" required minLength={8} {...register("password")}/></label><button className="passwordReveal" type="button" aria-label={showPassword?"Hide password":"Show password"} aria-pressed={showPassword} onClick={()=>setShowPassword(!showPassword)}>{showPassword?"Hide":"Show"}</button></div>
        <input type="hidden" value="Individual" {...register("role")}/>
        {error&&<div className="error" role="alert">{error}</div>}
        <button className="button" type="submit" disabled={isSubmitting}>{isSubmitting?"Creating account…":"Continue"}</button>
      </form>
      <p className="authNote">We verify new accounts before workspace access. Already registered? <Link href={authHref("/login",destination)}>Log in</Link>.</p>
  </AuthFrame>;
}
