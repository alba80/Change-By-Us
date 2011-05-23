import giveaminute.keywords as keywords
import giveaminute.project as project
import giveaminute.projectResource as resource
import giveaminute.location as mLocation
import framework.util as util
from framework.controller import *
from framework.image_server import *
from PIL import Image
import lib.web
import json

class CreateProject(Controller):
    def GET(self, action=None):
        if (action == 'keywords'):
            return self.getKeywordsJSON()
        elif (action == 'similar'):
            return self.getSimilarProjectsJSON()
        elif (action == 'resources'):
            return self.getSimilarResourcesJSON()
        else:
            locations_data = mLocation.getSimpleLocationDictionary(self.db)
            locations = dict(json = json.dumps(locations_data), data = locations_data)
            
            return self.render('create', {'locations':locations})
            
    def POST(self, action=None):
        if (action == 'photo'):
            imageId = self.uploadImage()
        
            return self.json(dict(thumbnail_id = imageId, success = (imageId != None) ))
        else:
            return self.newProject()  
        
    def newProject(self):
        if (self.user):
            owner_user_id = self.user.id
            title = self.request('title')
            description = self.request('text')
            organization = self.request('organization')
            locationId = util.try_f(int, self.request('location_id'), -1)
            imageId = self.request('image')
            keywords = [word.strip() for word in self.request('keywords').split(',')] if not util.strNullOrEmpty(self.request('keywords')) else []
            resourceIds = self.request('resources').split(',')
            isOfficial = self.user.isAdmin
            
            projectId = project.createProject(self.db, owner_user_id, title, description, ' '.join(keywords), locationId, imageId, isOfficial, organization)
            
            for resourceId in resourceIds:
                log.info("*** insert resource id %s" % resourceId)
                project.addResourceToProject(self.db, projectId, resourceId)
                
            if (projectId):
                return projectId
            else:
                log.error("*** couldn't create project")
                return False
        else:
            log.error("*** only logged in users can create projects")
            return False
                    
    def getKeywordsJSON(self):
        s = "%s %s" % (self.request('text'), self.request('title'))
        kw = keywords.getKeywords(self.db, s)
        
        log.info(kw)
        
        obj = dict(suggested_keywords=kw)
    
        return self.json(obj)    
        
    def getSimilarProjectsJSON(self):
        locationId = self.request('location_id')
        keywords = self.request('keywords').split(',') if self.request('keywords') else []
                
        if (locationId and len(keywords) > 0):
            projects = project.getProjects(self.db, keywords, locationId)
        elif (locationId):
            projects = project.getProjectsByLocation(self.db, locationId)
        elif (len(keywords) > 0):
            projects = project.getProjectsByKeywords(self.db, keywords)
        else:
            return None
        
        obj = dict(projects = projects)
        
        return self.json(obj)
        
    def getSimilarResourcesJSON(self):
        locationId = self.request('location')
        keywords = self.request('keywords').split(',') if self.request('keywords') else []
                
        if (locationId and len(keywords) > 0):
            resources = resource.getProjectResources(self.db, keywords, locationId)
        elif (locationId):
            resources = resource.getProjectResourcesByLocation(self.db, locationId)
        elif (len(keywords) > 0):
            resources = resource.getProjectResourcesByKeywords(self.db, keywords)
        else:
            return None
        
        obj = dict(resources = resources)
        
        return self.json(obj)
    
    def uploadImage(self):
        if (len(self.request('qqfile')) > 100):
            data = self.request('qqfile')
        else:
            data = web.data()
        
        imageId = ImageServer.add(self.db, data, 'giveaminute', [100, 100])
        
        return imageId
                        
    