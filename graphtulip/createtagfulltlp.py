from tulip import *
from py2neo import *
import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")


# todo create a unique Createtlp to avoid code duplication
class CreateTagFullTlp(object):
    def __init__(self, value, start, end, force_fresh):
        super(CreateTagFullTlp, self).__init__()
        print('Initializing')

        self.neo4j_graph = Graph(host=config['neo4j']['url'], user=config['neo4j']['user'], password=config['neo4j']['password'])
        self.tulip_graph = tlp.newGraph()
        self.tulip_graph.setName('opencare - tagToTag')
        # todo pass in parameters labels and colors
        self.labels = ["label", "label", "label"]
        self.colors = {"user_id": tlp.Color(51,122,183), "post_id": tlp.Color(92,184,92), "comment_id": tlp.Color(240, 173, 78), "tag_id": tlp.Color(200, 10, 10), "edges": tlp.Color(204, 204, 204)}
        self.filter_occ = value
        self.date_start = start
        self.date_end = end
        self.force_fresh = force_fresh

    # -----------------------------------------------------------
    # the updateVisualization(centerViews = True) function can be called
    # during script execution to update the opened views

    # the pauseScript() function can be called to pause the script execution.
    # To resume the script execution, you will have to click on the "Run script " button.

    # the runGraphScript(scriptFile, graph) function can be called to launch another edited script on a tlp.Graph object.
    # The scriptFile parameter defines the script name to call (in the form [a-zA-Z0-9_]+.py)

    # the main(graph) function must be defined
    # to run the script on the current graph
    # -----------------------------------------------------------

    # Can be used with nodes or edges
    def managePropertiesEntity(self, entTlp, entN4J, entProperties):
        # print 'WIP'
        for i in entN4J.properties:
            tmpValue = str(entN4J.properties[i])
            if i in self.labels:
                word = tmpValue.split(' ')
                if len(word) > 3:
                    tmpValue = "%s %s %s ..." % (word[0], word[1], word[2])
                entProperties["viewLabel"] = self.tulip_graph.getStringProperty("viewLabel")
                entProperties["viewLabel"][entTlp] = tmpValue
            if i in self.colors.keys():
                entProperties["viewColor"] = self.tulip_graph.getColorProperty("viewColor")
                entProperties["viewColor"][entTlp] = self.colors.get(i)
            if i in entProperties:
                entProperties[i][entTlp] = tmpValue
            else:
                # print type(tmpValue)
                entProperties[i] = self.tulip_graph.getStringProperty(i)
                # print 'i = ' + i
                # print 'has key ? ' + str(i in entProperties)
                entProperties[i][entTlp] = tmpValue

    def manageLabelsNode(self, labelsNode, nodeTlp, nodeN4J):
        # print "WIP"
        tmpArrayString = []
        for s in nodeN4J.properties:
            tmpArrayString.append(s)
        labelsNode[nodeTlp] = tmpArrayString


    # def manageLabelEdge(labelEdge,edgeTlp,edgeN4J):
    # 	labelEdge[edgeTlp] = edgeN4J.type

    # def testTransmmission(graph,node):
    # 	testNul = self.tulip_graph.getIntegerProperty("testNul")
    # 	strNul = "testNul"
    # 	exec(strNul)[node] = 1

    def create(self, private_gid):
        # Entities properties
        tmpIDNode = self.tulip_graph.getStringProperty("tmpIDNode")
        labelsNodeTlp = self.tulip_graph.getStringVectorProperty("labelsNodeTlp")
        labelEdgeTlp = self.tulip_graph.getStringProperty("labelEdgeTlp")
        entityType = self.tulip_graph.getStringProperty("entityType")
        nodeProperties = {}
        edgeProperties = {}
        indexTags = {}
        indexPosts = {}
        indexComments = {}

        if (not os.path.exists("%s%s.tlp" % (config['exporter']['tlp_path'], "TTT"))) or self.force_fresh == 1:
            # Prepare tags and posts request
            req = "MATCH (t:tag)<-[:REFERS_TO]-(a:annotation)-[:ANNOTATES]->(e: post) "
            req+= "WHERE e.timestamp >= %d AND e.timestamp <= %d " % (self.date_start, self.date_end)
            req+= "RETURN t.tag_id, e.post_id, t, e, count(t) as strength"
            result = self.neo4j_graph.run(req)

            # Get the posts
            print("Read Posts")
            for qr in result:
                if not qr[0] in indexTags:
                    n = self.tulip_graph.addNode()
                    indexTags[qr[0]] = n
                    tmpIDNode[n] = str(qr[0])
                    self.managePropertiesEntity(n, qr[2], nodeProperties)
                    self.manageLabelsNode(labelsNodeTlp, n, qr[2])
                    entityType[n] = "tag"
                if not qr[1] in indexPosts:
                    n = self.tulip_graph.addNode()
                    indexPosts[qr[1]] = n
                    tmpIDNode[n] = str(qr[1])
                    self.managePropertiesEntity(n, qr[3], nodeProperties)
                    self.manageLabelsNode(labelsNodeTlp, n, qr[3])
                    entityType[n] = "post"

                e = self.tulip_graph.addEdge(indexTags[qr[0]], indexPosts[qr[1]])

            # Prepare tags and comments request
            req = "MATCH (t:tag)<-[:REFERS_TO]-(a:annotation)-[:ANNOTATES]->(e: comment) "
            req+= "WHERE e.timestamp >= %d AND e.timestamp <= %d " % (self.date_start, self.date_end)
            req+= "RETURN t.tag_id, e.comment_id, t, e, count(t) as strength"
            result = self.neo4j_graph.run(req)

            # Get the comments
            print("Read Comments")
            for qr in result:
                if not qr[0] in indexTags:
                    n = self.tulip_graph.addNode()
                    indexTags[qr[0]] = n
                    tmpIDNode[n] = str(qr[0])
                    self.managePropertiesEntity(n, qr[2], nodeProperties)
                    self.manageLabelsNode(labelsNodeTlp, n, qr[2])
                    entityType[n] = "tag"
                if not qr[1] in indexComments:
                    n = self.tulip_graph.addNode()
                    indexComments[qr[1]] = n
                    tmpIDNode[n] = str(qr[1])
                    self.managePropertiesEntity(n, qr[3], nodeProperties)
                    self.manageLabelsNode(labelsNodeTlp, n, qr[3])
                    entityType[n] = "comment"

                e = self.tulip_graph.addEdge(indexTags[qr[0]], indexComments[qr[1]])
            tlp.saveGraph(self.tulip_graph, "%s%s.tlp" % (config['exporter']['tlp_path'], "PostCommentTag"))

            print("Compute Tag-Tag graph")
            edgeProperties["occ"] = self.tulip_graph.getIntegerProperty("occ")
            edgeProperties["TagTagSelection"] = self.tulip_graph.getBooleanProperty("TagTagSelection")
            edgeProperties["TagTagSelection"].setAllNodeValue(False)
            edgeProperties["TagTagSelection"].setAllEdgeValue(False)
            edgeProperties["viewLabel"] = self.tulip_graph.getStringProperty("viewLabel")
            edgeProperties["type"] = self.tulip_graph.getStringProperty("type")
            edgeProperties["viewColor"] = self.tulip_graph.getColorProperty("viewColor")
            edgeProperties["viewSize"] = self.tulip_graph.getSizeProperty("viewSize")
            edgeProperties['tag_1'] = self.tulip_graph.getStringProperty("tag_1")
            edgeProperties['tag_2'] = self.tulip_graph.getStringProperty("tag_2")
            for t1 in indexTags:
                edgeProperties["TagTagSelection"][indexTags[t1]] = True
                for p in self.tulip_graph.getOutNodes(indexTags[t1]):
                    if entityType[p] == "post" or entityType[p] == "comment":
                        for t2 in self.tulip_graph.getInNodes(p):
                            if indexTags[t1] != t2:
                                e=self.tulip_graph.existEdge(indexTags[t1], t2, False)
                                if e.isValid():
                                    edgeProperties["occ"][e] += 1
                                    edgeProperties["viewLabel"][e] = "occ ("+str(edgeProperties["occ"][e])+")"
                                    labelEdgeTlp[e] = "occ ("+str(edgeProperties["occ"][e])+")"
                                    e_val = edgeProperties['occ'][e]
                                    if e_val > edgeProperties["occ"][indexTags[t1]]:
                                        edgeProperties["occ"][indexTags[t1]] = e_val
                                        edgeProperties["viewSize"][indexTags[t1]] = tlp.Size(e_val, e_val, e_val)
                                    if e_val > edgeProperties["occ"][t2]:
                                        edgeProperties["occ"][t2] = e_val
                                        edgeProperties["viewSize"][t2] = tlp.Size(e_val, e_val, e_val)
                                else:
                                    e = self.tulip_graph.addEdge(indexTags[t1], t2)
                                    edgeProperties["occ"][e] = 1
                                    edgeProperties["TagTagSelection"][t2] = True
                                    edgeProperties["TagTagSelection"][e] = True
                                    edgeProperties["viewLabel"][e] = "occ ("+str(edgeProperties["occ"][e])+")"
                                    labelEdgeTlp[e] = "occ ("+str(edgeProperties["occ"][e])+")"
                                    edgeProperties["type"][e] = "curvedArrow"
                                    edgeProperties["viewColor"][e] = self.colors['edges']
                                    edgeProperties['tag_1'][e] = tmpIDNode[indexTags[t1]]
                                    edgeProperties['tag_2'][e] = tmpIDNode[t2]
            sg = self.tulip_graph.addSubGraph(edgeProperties["TagTagSelection"])
            tlp.saveGraph(sg, "%s%s.tlp" % (config['exporter']['tlp_path'], "TTT"))
        else:
            sg = tlp.loadGraph("%s%s.tlp" % (config['exporter']['tlp_path'], "TTT"))

        print("Filter occ")
        edgeProperties["occ"] = sg.getIntegerProperty("occ")
        for t in sg.getNodes():
            edgeProperties["occ"][t] = edgeProperties["occ"][t]/2
            for e in sg.getOutEdges(t):
                edgeProperties["occ"][e] = edgeProperties["occ"][e]/2
                if edgeProperties["occ"][e] < self.filter_occ:
                    sg.delEdge(e)
            if edgeProperties["occ"][t] < self.filter_occ:
                sg.delNode(t)

        print("Export")
        tlp.saveGraph(sg, "%s%s.tlp" % (config['exporter']['tlp_path'], private_gid))

