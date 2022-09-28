# Many2Many Tree

Modulo per l'utilizzo del widget ad albero sui campi many2one dove è presente una relazione gerarchica.  
Per utilizzare il widget è necessario inserire l'attributo **widget="m2m_tree"** sul campo many2many all'interno della relativa vista xml.  
Il comportamento del widget può essere customizzato mediante l'uso dell'attributo **options**:  
  
- **field_name**: valorizzare con il nome del campo che si intende visualizzare negli item della tree (solo se diverso da name)  
- **field_parent**: valorizzare con il nome del campo che è utilizzato per stabilire la relazione di parent e child tra item della tree (solo se diverso da parent_id)  
- **field_style**: valorizzare con il nome della classe css se si vuole mostrare un'icona diversa per gli item della tree  
- **field_checkable**: valorizzare con il nome del campo che è utilizzato per stabilire se la checkbox deve essere selezionabile  
- **all_checkable**: valorizzare con true se si vuole che tutti gli item siano selezionabili, in caso contrario solamente gli item che rappresentano le foglie del tree sono selezionabili  
- **field_typology**: valorizzare con il nome del campo che è utilizzato per stabilire la tipologia degli item  
- **uncheck_different_typology**: valorizzare con true se si vuole che alla selezione di un item vengano deselezionati gli item parent o child se hanno tipologia diversa  
- **order**: valorizzare con la lista dei nomi dei campi sulla base dei quali fare l'ordinamento degli item ("name,tipologia DESC")  
- **no_open**: valorizzare con True se si vuole inibire l'accesso ai dati dell'item quando è mostrato in modalità readonly  
- **limit**: valorizzare con il numero massimo di item visualizzabili nel tree  
  
Infine valorizzando nell'attributo **context** la chiave **disable_ids** seguita da una lista di id, le checkbox dei corrispondenti item saranno disabilitate.