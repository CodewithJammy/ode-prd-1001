when repo change on azure. then on github settings/secrets/actions  needs to add clientid, ,tenant and subscription.
Create Microsoft_AAD_RegisteredApps/ app registration FIC . 
after that need to provide contributor role>>>> in azure bash >>>>>>>>>>>>>>> az role assignment create \
  --assignee XXXXclientidXXXX \
  --role "Contributor" \
  --scope "/subscriptions/XXXXsubscriptionidXXXX"

  
