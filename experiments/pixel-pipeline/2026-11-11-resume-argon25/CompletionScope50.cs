using System;
// Exception handling must never skip the GPU completion path of submitted work.
public static class CompletionScope50 {
 public static void Record(Action candidate,Action<Exception> failed,Action completion){
  try{candidate();}catch(Exception error){failed(error);}finally{completion();}
 }
}
