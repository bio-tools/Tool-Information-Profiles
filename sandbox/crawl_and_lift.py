import urllib3
import requests
import json
import os
from rdflib import ConjunctiveGraph
from jinja2 import Template

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_shape():
    mapping_attributes_bioschema = {}
    mapping_attributes_bioschema['name'] = "schema:name"  # done
    mapping_attributes_bioschema['description'] = "schema:description"  # done
    mapping_attributes_bioschema['homepage'] = "schema:url"  # done
    # mapping_attributes_bioschema['biotoolsID'] = ""
    # mapping_attributes_bioschema['biotoolsCURIE'] = ""
    mapping_attributes_bioschema['toolType'] = "schema:additionalType"  # done
    mapping_attributes_bioschema['topic'] = "schema:applicationSubCategory"  # done
    mapping_attributes_bioschema['cost'] = "schema:isAccessibleForFree"  # done
    mapping_attributes_bioschema['publicationPrimary'] = "schema:citation"  # done
    mapping_attributes_bioschema['creditprimaryContact'] = "biotools:primaryContact"  # done
    mapping_attributes_bioschema['operation'] = "schema:featureList"  # done
    mapping_attributes_bioschema['inputData'] = "edam:has_input"  # done
    mapping_attributes_bioschema['outputData'] = "edam:has_output"  # done
    mapping_attributes_bioschema['operatingSystem'] = "schema:operatingSystem"  # done
    mapping_attributes_bioschema['license'] = "schema:license"  # done
    mapping_attributes_bioschema['apiDocumentation'] = "schema:softwareHelp"  # done
    mapping_attributes_bioschema['generalDocumentation'] = "schema:softwareHelp"  # done
    # mapping_attributes_bioschema['commandlineOptions'] = "biotools:commandlineOptions" # any availabe ?
    mapping_attributes_bioschema['termsOfUse'] = "schema:termsOfService"  # any availabe ?

    mandatory_rules = []
    with open('../../profiles/ifbToolInfoProfile.json', 'r') as f:
        profile = json.load(f)
    for r in profile['rules']:
        if 'Mandatory' in r['requirement']:
            print(r)
            std_attributes = []
            for at in r['attributes']:
                # 1. Loading an information profile     if at in mapping_attributes_bioschema.keys():
                if at in mapping_attributes_bioschema.keys():
                    std_attributes.append(mapping_attributes_bioschema[at])
            r['attributes'] = std_attributes
            print(r)
            mandatory_rules.append(r)
            print()
            print()

    shape_template = """
    @prefix dash: <http://datashapes.org/dash#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix schema: <http://schema.org/> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix edam: <http://edamontology.org/> .
    @prefix biotools: <https://bio.tools/ontology/> .

    {% for rule in rules %}
    schema:ToolShape
        a sh:NodeShape ;
        sh:targetClass schema:SoftwareApplication ;

        sh:filterShape [
            sh:property [
                sh:path schema:additionalType ;
                sh:in ( {% for type in rule['types'] %} "{{ type }}" {% endfor %} ) ;
            ] ;
        ] ;

        {% for prop_name in rule['attributes'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
        ] ;
        {% endfor %}
        .
    {% endfor %}
    """

    template = Template(shape_template)
    shape = template.render(rules=mandatory_rules)
    print(shape)
    g = ConjunctiveGraph()
    g.parse(data=shape, format='turtle')
    print(len(g))
    return g

def rdfize(json_entry):
    """
    Transforms a biotools json entry into RDF, and returns a JSON-LD serialization. The following fields
    are covered: contact, publication, EDAM topic, EDAM operation, EDAM inputs & outputs.
    """

    entry = json_entry

    try:

        ctx = {
            "@context": {
                "@base": "https://bio.tools/",
                "biotools": "https://bio.tools/ontology/",
                "edam": "http://edamontology.org/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "sc": "http://schema.org/", 
                "bsc": "http://bioschemas.org/",
                
                "description": 'sc:description',
                "name": "sc:name",
                "homepage": "sc:url",
                "toolType": 'sc:additionalType',
                
                
                "primaryContact": 'biotools:primaryContact',
                "author": 'sc:author',
                "provider": 'sc:provider',
                "contributor": 'sc:contributor',
                "funder": 'sc:funder',
                "hasPublication": "sc:citation",
                
                "hasTopic": 'sc:applicationSubCategory',
                "hasOperation": "sc:featureList",
                "hasInputData": "edam:has_input",
                "hasOutputData": "edam:has_output",
                
                "license": "sc:license",
                "version": "sc:version",
                "isAccessibleForFree" : "sc:isAccessibleForFree",
                "operatingSystem": "sc:operatingSystem",
                "hasApiDoc": "sc:softwareHelp",
                "hasGenDoc": "sc:softwareHelp",
                "hasTermsOfUse": "sc:termsOfService",
                
            }
        }
        entry.update(ctx)
        
        entry['@id'] = str(entry['biotoolsID'])
        #entry['@type'] = ['bsc:Tool','sc:SoftwareApplication']
        entry['@type'] = ['sc:SoftwareApplication']
        entry['applicationCategory'] = 'Computational science tool'
        entry['primaryContact'] = []
        entry['author'] = []
        entry['contributor'] = []
        entry['provider'] = []
        entry['funder'] = []

        
        for credit in entry['credit']:
            #print(credit)
            
            ## Retrieving FUNDERS
            if 'typeEntity' in credit.keys() and credit['typeEntity']:
                if 'Funding agency' in credit['typeEntity']:
                    sType = "schema:Organization"
                    if 'orcidid' in credit.keys() and credit['orcidid'] != None :
                        if not 'funder' in entry.keys():
                            entry['funder'] = {"@id":credit['orcidid'], "@type":sType}
                        else:
                            entry['funder'].append({"@id":credit['orcidid'], "@type":sType})        
                    elif 'name' in credit.keys() and credit['name'] != None:
                        if not 'funder' in entry.keys():
                            entry['funder'] = [credit['name']]
                        else:
                            entry['funder'].append(credit['name'])
            
            #Retrieving CONTRIBUTORS, PROVIDERS, DEVELOPERS
            if credit['typeRole']:
                if 'Developer' in credit['typeRole']:
                    #print("**** DEVELOPER ****")
                    #print(credit['name'])
                    if 'typeEntity' in credit.keys() and credit['typeEntity']:
                        if 'Person' in credit['typeEntity']:
                            sType = "schema:Person"
                        else:
                            sType = "schema:Organization"
                        if 'orcidid' in credit.keys() and credit['orcidid'] != None :
                            if not 'author' in entry.keys():
                                entry['author'] = {"@id":credit['orcidid'], "@type":sType}
                            else:
                                entry['author'].append({"@id":credit['orcidid'], "@type":sType})        
                        elif 'name' in credit.keys() and credit['name'] != None:
                            if not 'author' in entry.keys():
                                entry['author'] = [credit['name']]
                            else:
                                entry['author'].append(credit['name'])
                    else:
                        if 'name' in credit.keys() and credit['name'] != None:
                            if not 'author' in entry.keys():
                                entry['author'] = [credit['name']]
                            else:
                                entry['author'].append(credit['name'])
                                
                if 'Provider' in credit['typeRole']:
                    #print("**** PROVIDER ****")
                    #print(credit['name'])
                    if 'typeEntity' in credit.keys() and credit['typeEntity']:
                        if 'Person' in credit['typeEntity']:
                                sType = "schema:Person"
                        else:
                            sType = "schema:Organization"

                        if 'orcidid' in credit.keys() and credit['orcidid'] != None :
                            if not 'provider' in entry.keys():
                                entry['provider'] = {"@id":credit['orcidid'], "@type":sType}
                                #if 'name' in credit.keys() and credit['name'] != None:
                                #    entry['author_person']['name'] = credit['name']
                            else:
                                entry['provider'].append({"@id":credit['orcidid'], "@type":sType})        
                        elif 'name' in credit.keys() and credit['name'] != None:
                            if not 'provider' in entry.keys():
                                entry['provider'] = [credit['name']]
                            else:
                                entry['provider'].append(credit['name'])
                    else:
                        if 'name' in credit.keys() and credit['name'] != None:
                            if not 'provider' in entry.keys():
                                entry['provider'] = [credit['name']]
                            else:
                                entry['provider'].append(credit['name'])
                
                if 'Contributor' in credit['typeRole']:
                    #print("**** CONTRIBUTOR ****")
                    #print(credit['name'])
                    
                    if 'typeEntity' in credit.keys() and credit['typeEntity']:
                        if 'Person' in credit['typeEntity']:
                            sType = "schema:Person"
                        else:
                            sType = "schema:Organization"
                        
                        if 'orcidid' in credit.keys() and credit['orcidid'] != None :
                            if not 'contributor' in entry.keys():
                                entry['contributor'] = {"@id":credit['orcidid'], "@type":sType}
                            else:
                                entry['contributor'].append({"@id":credit['orcidid'], "@type":sType})        
                        elif 'name' in credit.keys() and credit['name'] != None:
                            if not 'contributor' in entry.keys():
                                entry['contributor'] = [credit['name']]
                            else:
                                entry['contributor'].append(credit['name'])
                    else:
                        if 'name' in credit.keys() and credit['name'] != None:
                            if not 'contributor' in entry.keys():
                                entry['contributor'] = [credit['name']]
                            else:
                                entry['contributor'].append(credit['name'])  
                
                if 'Primary contact' in credit['typeRole']:
                    #print("**** CONTRIBUTOR ****")
                    #print(credit['name'])
                    
                    if 'typeEntity' in credit.keys() and credit['typeEntity']:
                        if 'Person' in credit['typeEntity']:
                            sType = "schema:Person"
                        else:
                            sType = "schema:Organization"
                        
                        if 'orcidid' in credit.keys() and credit['orcidid'] != None :
                            if not 'primaryContact' in entry.keys():
                                entry['primaryContact'] = {"@id":credit['orcidid'], "@type":sType}
                            else:
                                entry['primaryContact'].append({"@id":credit['orcidid'], "@type":sType})        
                        elif 'name' in credit.keys() and credit['name'] != None:
                            if not 'primaryContact' in entry.keys():
                                entry['primaryContact'] = [credit['name']]
                            else:
                                entry['primaryContact'].append(credit['name'])
                    else:
                        if 'name' in credit.keys() and credit['name'] != None:
                            if not 'primaryContact' in entry.keys():
                                entry['primaryContact'] = [credit['name']]
                            else:
                                entry['primaryContact'].append(credit['name'])      
            
            
            
        for publication in entry['publication']:
            if publication['pmid']:
                if not "hasPublication" in entry.keys():
                    #entry['hasPublication'] = [{"@id": 'pubmed:' + publication['pmid']}]
                    entry['hasPublication'] = ['pubmed:' + publication['pmid']]
                else:
                    #entry['hasPublication'].append({"@id": 'pubmed:' + publication['pmid']})
                    entry['hasPublication'].append('pubmed:' + publication['pmid'])
            if publication['pmcid']:
                if not "hasPublication" in entry.keys():
                    entry['hasPublication'] = ['pmcid:' + publication['pmcid']]
                else:
                    entry['hasPublication'].append('pmcid:' + publication['pmcid'])
            if publication['doi']:
                if not ("<" in publication['doi'] or ">" in publication['doi']):
                    if not "hasPublication" in entry.keys():
                        entry['hasPublication'] = [{"@id": "https://doi.org/" + publication['doi'], "@type":"sc:CreativeWork"}]
                    else:
                        entry['hasPublication'].append({"@id": "https://doi.org/" + publication['doi'], "@type":"sc:CreativeWork"})

        for item in entry['function']:
            for op in item['operation']:
                if not "hasOperation" in entry.keys():
                    entry['hasOperation'] = [{"@id": op['uri']}]
                else:
                    entry['hasOperation'].append({"@id": op['uri']})

            for input in item['input']:
                if not "hasInputData" in entry.keys():
                    entry['hasInputData'] = [{"@id": input['data']['uri']}]
                else:
                    entry['hasInputData'].append({"@id": input['data']['uri']})

            for output in item['output']:
                if not "hasOutputData" in entry.keys():
                    entry['hasOutputData'] = [{"@id": output['data']['uri']}]
                else:
                    entry['hasOutputData'].append({"@id": output['data']['uri']})

        for item in entry['topic']:
            if not "hasTopic" in entry.keys():
                entry['hasTopic'] = [{"@id": item['uri']}]
            else:
                entry['hasTopic'].append({"@id": item['uri']})
                
        if entry['cost']:
            for item in entry['cost']:
                if not "isAccessibleForFree" in entry.keys():
                    if "Free" in entry['cost'] : 
                        entry['isAccessibleForFree'] = True
                    else:
                        entry['isAccessibleForFree'] = False
                    
        for item in entry['documentation']:
            if 'type' in item.keys() and item['type']:
                if 'API' in item['type']:
                    if not 'hasApiDoc' in entry.keys():
                        entry['hasApiDoc'] = [{"@id": item['url']}]
                    else:
                        entry['hasApiDoc'].append({"@id": item['url']})
                elif 'Terms' in item['type']:
                    if not 'hasTermsOfUse' in entry.keys():
                        entry['hasTermsOfUse'] = [{"@id": item['url']}]
                    else:
                        entry['hasTermsOfUse'].append({"@id": item['url']})
                else:
                    if not 'hasGenDoc' in entry.keys():
                        entry['hasGenDoc'] = [{"@id": item['url']}]
                    else:
                        entry['hasGenDoc'].append({"@id": item['url']})
                

    except KeyError as error:
        print(error)
        #print(json.dumps(entry, indent=4, sort_keys=True))
        print()
        
    #print(json.dumps(entry, indent=4, sort_keys=True))

    raw_jld = json.dumps(entry, indent=4, sort_keys=True)
    return raw_jld

def get_tool_count():
    http = urllib3.PoolManager()
    http.headers['Accept'] = 'application/json'
    http.headers['Content-type'] = 'application/json'
    req = http.request('GET', 'https://bio.tools/api/tool/?page=1&?format=json')

    count_json = json.loads(req.data.decode('utf-8'))
    count = int(count_json['count'])

    print(str(count) + " available BioTools entries")

    return count


def crawl_biotools(collection="", limit=-1, dump=False):
    graph = ConjunctiveGraph()
    
    """
    Go through all bio.tools entries and produce an RDF graph representation (BioSchemas / JSON-LD).  
    :param limit: an integer value specifying the max number of entries to be crawled, -1 by default, means no limit.
    """
    
    http = urllib3.PoolManager()
    http.headers['Accept'] = 'application/json'
    http.headers['Content-type'] = 'application/json'
    
    try:
        
        #url = 'https://bio.tools/api/tool/?page=1&?format=json'
        #r = requests.get(url)
        #print(r.json())
        #count_json = r.json()
        
        count = get_tool_count()

        i = 1
        nb_tools = 1
        has_next_page = True
        while has_next_page :
            if collection:
                req = http.request('GET', 'https://bio.tools/api/tool/?collectionID=' + str(collection) + '&page=' + str(i) + '&format=json')
            else:
                req = http.request('GET', 'https://bio.tools/api/tool/?page=' + str(i) + '&format=json')
            try:
                entry = json.loads(req.data.decode('utf-8'))
            except JSONDecodeError as e:
                print("Json decode error for " + str(req.data.decode('utf-8')))
                break
            has_next_page = (entry['next'] != None)

            for tool in entry['list']:
                jsonld = rdfize(tool)
                graph.parse(data=jsonld, format='json-ld')
                
                if dump:
                    temp_graph = ConjunctiveGraph()
                    temp_graph.parse(data=jsonld, format='json-ld')
                    os.makedirs('./bio.tools.dataset/'+tool['biotoolsID'], exist_ok=True)
                    temp_graph.serialize(format="json-ld", auto_compact=True, destination=str('./bio.tools.dataset/'+tool['biotoolsID']+'/'+tool['biotoolsID']+'.jsonld'))
                    
                nb_tools += 1
                progress = nb_tools * 100 / count
                if (nb_tools % 500 == 0) :
                    print(str(round(progress))+" % done")
                if ((limit != -1) and (nb_tools >= limit)):
                    return graph
            i += 1

    except urllib3.exceptions.HTTPError as e:
        print(e)
    
    return graph