type ReservationV1 = {reservationId:string;operationId:string;equipmentId:string;quantity:number;state:string};
let reservation:ReservationV1|null=null;
const button=(id:string)=>document.getElementById(id) as HTMLButtonElement;
const message=document.getElementById('error')!;
async function send(path:string, body:object):Promise<void>{
  message.textContent='';
  const response=await fetch('/api/v1/reservations'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok){message.textContent=response.status===400?'Confirm your acknowledgement before continuing.':'This reservation cannot be changed.';return;}
  reservation=await response.json() as ReservationV1;
  document.getElementById('state')!.textContent=reservation.state;
  button('confirm').disabled=button('cancel').disabled=reservation.state!=='Reserved';
}
button('reserve').onclick=()=>void send('',{operationId:crypto.randomUUID(),equipmentId:'camera',quantity:1});
button('confirm').onclick=()=>{if(reservation)void send('/'+reservation.reservationId+'/confirm',{operationId:crypto.randomUUID(),acknowledged:(document.getElementById('ack') as HTMLInputElement).checked});};
button('cancel').onclick=()=>{if(reservation)void send('/'+reservation.reservationId+'/cancel',{operationId:crypto.randomUUID()});};
