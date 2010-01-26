#!/bin/sh

### Erzeuge Informationen über alle ausstehenden Transaktionen aller
### Subversion Repositorys.

REPOPATH=/srv/svn

for REPOS in $REPOPATH/*; do
    for TXN in `svnadmin lstxns ${REPOS}`; do
        echo "---[ found stale transaction: ${TXN} ]-------------------------------------------"
        echo "Repository: ${REPOS}"
        svnlook info "${REPOS}" -t "${TXN}"
        echo "Changes:"
        svnlook changed "${REPOS}" -t "${TXN}"
    done
done

