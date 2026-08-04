# Llave de la forja (token GitHub) — solo Monarca

El Cursor del VPS pide token porque quiere **subir** cambios (`git push`).  
Eso **no** se guarda en el repo: tú creas la llave y se la pegas **en el chat** del VPS.

## Crear la llave (2 minutos)

1. Abre: https://github.com/settings/tokens?type=beta  
   (o: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained**)
2. **Generate new token**
   - Nombre: `ShadowHarmy-VPS`
   - Caducidad: 30–90 días (luego renuevas)
   - Repository access: **Only select** → `ShadowHarmy`
   - Permissions → Repository → **Contents: Read and write**  
     (si pide Metadata: Read, déjalo)
3. Generar → **copiar el token una sola vez** (empieza por `github_pat_…`)

## Alternativa clásica (más ancha)

https://github.com/settings/tokens → Classic → `repo` (todo el alcance repo). Solo si la fine-grained falla.

## Cómo dársela al Cursor del VPS

En el mensaje que le pegas, sustituye `PEGAR_TOKEN_AQUI` por ese valor.  
**Nunca** lo commits, ni lo dejes en un `.md` del ejército.

Cuando el VPS ya no necesite push (solo túnel), puedes **revocar** el token en la misma página.
