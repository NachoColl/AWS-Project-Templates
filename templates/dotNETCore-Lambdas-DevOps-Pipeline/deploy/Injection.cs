using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

using Newtonsoft.Json;
using nWAY.Library;

namespace deploy
{
    class Injection
    {
        public class AWSAPIMethodInfo{
            public string MethodName;
            public string MethodPath;
        }

        // args[0]: assembly file full path
        // args[1]: cloudformation files path
        // args[2]: environment (staging / prod)
        // args[3]: build version
        // args[4]: 0: new env stack, 1:already exists
        static int Main(string[] args)
        {

            try{

                /*
                    Inject resources to BASE template.
                 */
                string samFile = string.Format("{0}/sam.yml", args[1]);
                string samBaseFile = string.Format("{0}/sam-base.yml", args[1]);

                // Get the list of defined functions from assembly.
                List<AWSAPIMethodInfo> functions = GetFunctions(args[0]);

                // Build the cloudformation BASE resources string to inject.
                string cloudformationBaseResources = GetCloudformationBaseResourcesString(functions);

                string source = System.IO.File.ReadAllText(samFile);   
                if (File.Exists(samBaseFile)) File.Delete(samBaseFile);
                using (FileStream fs = System.IO.File.Create(samBaseFile))
                {
                    Byte[] info = new UTF8Encoding(true).GetBytes(source.Replace("@INJECT"," INJECTED CODE:" + cloudformationBaseResources + IndentText(1,"# END of injected code")));
                    fs.Write(info, 0, info.Length);
                }


                /*
                    Inject resources to ENVIRONMENT template.
                */
                string environment = args[2];
                int buildVersion = Int32.Parse(args[3]);
                bool newStack = args[4].Equals("0");
                
                string samXFile = string.Format("{0}/samx.yml", args[1]);
                string samEnvironmentFile = string.Format("{0}/sam-{1}.yml", args[1], environment);
             
                // Build the cloudformation ENVIRONMENT resources string to inject.      
                string cloudformationEnvironmentResources = GetCloudformationEnvironmentResourcesString(functions, environment, buildVersion, newStack);

                string sourceX = System.IO.File.ReadAllText(samXFile);   
                if (File.Exists(samEnvironmentFile)) File.Delete(samEnvironmentFile);
                using (FileStream fs = System.IO.File.Create(samEnvironmentFile))
                {
                    Byte[] info = new UTF8Encoding(true).GetBytes(sourceX.Replace("@INJECT"," INJECTED CODE:" + cloudformationEnvironmentResources + IndentText(1,"# END of injected code")));
                    fs.Write(info, 0, info.Length);
                }

                return 0;
            } catch(Exception e){
                Console.WriteLine(e.Message);
                return -1;
            }
        }

        static List<AWSAPIMethodInfo> GetFunctions(string AssemblyFile){
            List<AWSAPIMethodInfo> functionsList = new List<AWSAPIMethodInfo>();
            Assembly testAssembly = Assembly.LoadFile(AssemblyFile);
            foreach (Type type in testAssembly.GetTypes()) 
            {   
                foreach (MethodInfo methodInfo in type.GetMethods()
                            .Where(m => !typeof(object)
                            .GetMethods()
                            .Select(me => me.Name)
                            .Contains(m.Name))){

                    AWSApiGatewayProperties apiGatewayPath= (AWSApiGatewayProperties) methodInfo.GetCustomAttribute(typeof (AWSApiGatewayProperties));
                    functionsList.Add(new AWSAPIMethodInfo(){ MethodName = methodInfo.Name, MethodPath = apiGatewayPath?.Path ?? methodInfo.Name});
                }
            }
            return functionsList;
        }

        static string GetCloudformationBaseResourcesString(List<AWSAPIMethodInfo> functions){
            // the cloudformation deployment resrouces.
            StringBuilder cloudformationResources = new StringBuilder();
            cloudformationResources.AppendLine();

            foreach(AWSAPIMethodInfo function in functions){

                cloudformationResources.AppendLine();
                cloudformationResources.AppendLine(IndentText(1, String.Format("{0}Function:", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(2, "Type: AWS::Serverless::Function"));
                cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                cloudformationResources.AppendLine(IndentText(3, String.Format("FunctionName: nway-{0}", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(3, String.Format("Handler: nwayapi::nWAY.API::{0} ", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(3, "Role: !Sub \"arn:aws:iam::${AWS::AccountId}:role/nway-lambdas\""));
                cloudformationResources.AppendLine();

                cloudformationResources.AppendLine();
                cloudformationResources.AppendLine(IndentText(1, String.Format("{0}APIResource:", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(2, "Type: AWS::ApiGateway::Resource"));
                cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                cloudformationResources.AppendLine(IndentText(3, "RestApiId: !Ref nWAYApi"));
                cloudformationResources.AppendLine(IndentText(3, "ParentId: !GetAtt nWAYApi.RootResourceId"));
                cloudformationResources.AppendLine(IndentText(3, String.Format("PathPart: {0}", function.MethodPath)));
                cloudformationResources.AppendLine();

                cloudformationResources.AppendLine();
                cloudformationResources.AppendLine(IndentText(1, String.Format("{0}APIMethod:", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(2, "Type: AWS::ApiGateway::Method"));
                cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                cloudformationResources.AppendLine(IndentText(3, "RestApiId: !Ref nWAYApi"));
                cloudformationResources.AppendLine(IndentText(3, String.Format("ResourceId: !Ref {0}APIResource", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(3, "HttpMethod: POST"));
                cloudformationResources.AppendLine(IndentText(3, "AuthorizationType: NONE"));
                cloudformationResources.AppendLine(IndentText(3, "Integration:"));
                cloudformationResources.AppendLine(IndentText(4, "Type: AWS_PROXY"));
                cloudformationResources.AppendLine(IndentText(4, "IntegrationHttpMethod: POST"));
                cloudformationResources.AppendLine(IndentText(4, "Uri: !Sub \"arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${" + function.MethodName + "Function.Arn}:${!stageVariables.lambdaAlias}/invocations\""));
                cloudformationResources.AppendLine(IndentText(4, "Credentials: !Sub \"arn:aws:iam::${AWS::AccountId}:role/nway-lambdas\""));
                cloudformationResources.AppendLine();

                
            }

            // StagingDeployment
            cloudformationResources.AppendLine();
            cloudformationResources.AppendLine(IndentText(1, "StagingDeployment:"));
            cloudformationResources.AppendLine(IndentText(2, "Type: AWS::ApiGateway::Deployment"));
            cloudformationResources.AppendLine(IndentText(2, "Properties:"));
            cloudformationResources.AppendLine(IndentText(3, "RestApiId: !Ref nWAYApi"));
            cloudformationResources.AppendLine(IndentText(2, "DependsOn:"));
            foreach(AWSAPIMethodInfo function in functions){
                    cloudformationResources.AppendLine(IndentText(3, String.Format("- {0}APIMethod", function.MethodName)));
            }
            cloudformationResources.AppendLine();

            // ProdDeployment
            cloudformationResources.AppendLine();
            cloudformationResources.AppendLine(IndentText(1, "ProdDeployment:"));
            cloudformationResources.AppendLine(IndentText(2, "Type: AWS::ApiGateway::Deployment"));
            cloudformationResources.AppendLine(IndentText(2, "Properties:"));
            cloudformationResources.AppendLine(IndentText(3, "RestApiId: !Ref nWAYApi"));
            cloudformationResources.AppendLine(IndentText(2, "DependsOn:"));
             foreach(AWSAPIMethodInfo function in functions){
                    cloudformationResources.AppendLine(IndentText(3, String.Format("- {0}APIMethod", function.MethodName)));
            }
            cloudformationResources.AppendLine();

            return cloudformationResources.ToString();
        }

        static string GetCloudformationEnvironmentResourcesString(List<AWSAPIMethodInfo> functions, string Environment, int BuildVersion, bool NewStack){

            StringBuilder cloudformationResources = new StringBuilder();
            cloudformationResources.AppendLine();

            // staging and prod on the same account
            // staging will use odd numbers (2 lambda versions)
            // prod will use even numbers (also 2 lambda versions)
            int environmentVersion1=Environment.Equals("staging") ? BuildVersion + (BuildVersion - 1) : BuildVersion * 2,
                environmentVersion2=environmentVersion1 + 2;

            foreach(AWSAPIMethodInfo function in functions){

                if (!NewStack){

                    cloudformationResources.AppendLine();
                    cloudformationResources.AppendLine(IndentText(1, String.Format("{0}Version{1}:", function.MethodName, environmentVersion1)));
                    cloudformationResources.AppendLine(IndentText(2, "Type: AWS::Lambda::Version"));
                    cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                    cloudformationResources.AppendLine(IndentText(3, String.Format("FunctionName: nway-{0}", function.MethodName)));
                    cloudformationResources.AppendLine();
                }

                cloudformationResources.AppendLine();
                cloudformationResources.AppendLine(IndentText(1, String.Format("{0}Version{1}:", function.MethodName, environmentVersion2)));
                cloudformationResources.AppendLine(IndentText(2, "Type: AWS::Lambda::Version"));
                cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                cloudformationResources.AppendLine(IndentText(3, String.Format("FunctionName: nway-{0}", function.MethodName)));
                cloudformationResources.AppendLine();

                cloudformationResources.AppendLine();
                cloudformationResources.AppendLine(IndentText(1, String.Format("{0}Alias:", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(2, "Type: AWS::Lambda::Alias"));
                cloudformationResources.AppendLine(IndentText(2, "Properties:"));
                cloudformationResources.AppendLine(IndentText(3, String.Format("FunctionName: nway-{0}", function.MethodName)));
                cloudformationResources.AppendLine(IndentText(3, String.Format("FunctionVersion: !GetAtt {0}Version{1}.Version", function.MethodName, environmentVersion2)));
                cloudformationResources.AppendLine(IndentText(3, String.Format("Name: {0}", Environment)));
                cloudformationResources.AppendLine();
                
            }

            return cloudformationResources.ToString();
        }

        static string IndentText(int Level, string Text) => String.Concat(new string(' ', Level * 2), Text);

        static bool IsOdd(int value) => value % 2 != 0;
   
    }
}
